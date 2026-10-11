"""Bounded in-memory inspection jobs. No screenshots or reports written to disk."""
import copy
import threading
import time
import uuid
from interface_inspection import PANELS, validate_request
from inspection_runtime import stamp


class InspectionJobs:
    def __init__(self):
        self.lock = threading.RLock()
        self.jobs = {}

    def start(self, request, runner, summarizer=None, budget=900, on_finish=None):
        request = validate_request(request)
        with self.lock:
            self._clean()
            if any(j['status'] == 'running' or j.get('archive',{}).get('status')=='pending' for j in self.jobs.values()):
                raise ValueError('An inspection job is already running.')
            while len(self.jobs) >= 2:
                del self.jobs[next(iter(self.jobs))]
            key = uuid.uuid4().hex
            panels = list(PANELS) if request['panel'] == 'all' else [request['panel']]
            job = dict(id=key, request=request, status='running', requested_at=stamp(), finished_at=None,
                       panels=panels, current_panel=None, results=[], review='', review_status='pending', archive={'status':'pending' if on_finish else 'disabled'},
                       errors=[], cancel=threading.Event(), expires=time.monotonic()+budget+300)
            self.jobs[key] = job
        threading.Thread(target=self._work, args=(key, request, runner, summarizer, budget, on_finish), daemon=True).start()
        return {'job_id': key, 'panels': panels, 'status': 'requested'}

    def _clean(self):
        for key in list(self.jobs):
            if self.jobs[key]['expires'] < time.monotonic() and self.jobs[key]['status'] != 'running':
                del self.jobs[key]

    def get(self, key):
        with self.lock:
            self._clean()
            if key not in self.jobs:
                raise ValueError('Inspection job expired or unavailable.')
            result=copy.deepcopy({k:v for k,v in self.jobs[key].items() if k not in ('cancel','expires')})
            if result.get('archive',{}).get('status')=='pending' and result['status']!='running':
                result['status']='running'
                result['phase']='archiving'
            return result

    def cancel(self, key):
        with self.lock:
            if key not in self.jobs:
                raise ValueError('Inspection job expired or unavailable.')
            self.jobs[key]['cancel'].set()
        return {'status':'cancellation_requested', 'job_id':key}

    def _work(self, key, request, runner, summarizer, budget, on_finish=None):
        job = self.jobs[key]
        deadline = time.monotonic()+budget
        try:
            for panel in job['panels']:
                if job['cancel'].is_set() or time.monotonic() >= deadline:
                    break
                with self.lock:
                    job['current_panel'] = panel
                try:
                    result = runner({**request, 'panel':panel}, job['cancel'])
                except Exception:
                    result = {'requested_panel':panel, 'assessment_mode':'none', 'errors':['Panel inspection failed.'], 'stages':{}}
                result['finished_at'] = stamp()
                stages = result.get('stages', {})
                result['status'] = (('partially_analysed' if result.get('coverage_limited') else 'analysed') if stages.get('analysis_completed') == 'completed' else
                                    'captured' if stages.get('screenshot_captured') == 'completed' else 'failed')
                with self.lock:
                    job['results'].append(result)
            with self.lock:
                job['current_panel'] = None
                results = copy.deepcopy(job['results'])
            # A faithful combined report remains available even if synthesis fails.
            review = '\n\n'.join(r['requested_panel'].upper()+' — '+r['status']+'\n'+r.get('analysis','No visual analysis completed.') for r in results)
            review_status = 'combined_panel_reports'
            analysed = [r for r in results if r['status'] in ('analysed','partially_analysed')]
            if summarizer and analysed and not job['cancel'].is_set() and time.monotonic() < deadline:
                try:
                    consolidated = summarizer(analysed, job['cancel'])
                    if not isinstance(consolidated,str) or not consolidated.strip():
                        raise ValueError('Empty consolidated review')
                    review = consolidated
                    review_status = 'consolidated'
                except Exception:
                    with self.lock: job['errors'].append('Consolidation unavailable; individual panel findings retained.')
            with self.lock:
                job['review'] = review
                job['review_status'] = review_status
                job['status'] = ('cancelled' if job['cancel'].is_set() else 'timed_out' if time.monotonic() >= deadline else
                                 'completed' if len(analysed)==len(job['panels']) and all(r['status']=='analysed' for r in results) else 'partial')
        except Exception:
            with self.lock:
                job['status']='failed'
                job['errors'].append('Inspection job failed; completed panel results retained.')
        finally:
            with self.lock:
                job['finished_at']=stamp()
                job['expires']=time.monotonic()+300
            if on_finish:
                with self.lock: finished=copy.deepcopy({k:v for k,v in job.items() if k not in ('cancel','expires')})
                try: archived=on_finish(finished)
                except Exception: archived={'status':'failed','error':'Archiving failed; temporary report retained. Check the improvement project and local storage.'}
                with self.lock: job['archive']=archived
            cleanup=threading.Timer(301,self._expire,args=(key,))
            cleanup.daemon=True
            cleanup.start()

    def _expire(self,key):
        with self.lock:
            if key in self.jobs and self.jobs[key]['expires'] <= time.monotonic():
                del self.jobs[key]


JOBS = InspectionJobs()
