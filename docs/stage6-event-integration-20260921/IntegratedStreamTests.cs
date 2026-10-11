using System;
using System.Diagnostics;
using System.IO;
using System.Text;
using System.Threading;
public static class IntegratedStreamTests {
 static void Save(string p,string text){using(var f=new FileStream(p,FileMode.CreateNew,FileAccess.Write,FileShare.Read)){var b=Encoding.UTF8.GetBytes(text);f.Write(b,0,b.Length);f.Flush(true);}}
 public static string Run(string root,int events,int padding) {
  EventTap.Initialize(root);var w=Stopwatch.StartNew();int completed=0;
  for(int i=0;i<events;i++){
   var row=new TapRow{pid=100,parentPid=50,kind=i%2==0?"start":"stop",stage="A-callback",name="SYNTHETIC_CAPACITY_ONLY"+new string('x',padding),nativeTime="100",eventId=i,source="generated-test",queueDepth=0};
   if(!EventTap.Record(row))break;
   row=new TapRow{pid=100,parentPid=50,kind=i%2==0?"start":"stop",stage="A-enqueue",name=row.name,nativeTime="100",eventId=i,source="generated-test",queueDepth=0};
   if(!EventTap.Record(row))break;
   string raw="{\"source\":\"CIM_PROCESS_NOTIFICATION\",\"kind\":"+AuthoritativeEvents.Quote(row.kind)+",\"pid\":100,\"parentPid\":50,\"name\":"+AuthoritativeEvents.Quote(row.name)+",\"nativeTime\":\"100\",\"eventIdentifier\":"+i+",\"queueSequence\":"+(i+1)+",\"receivedQpc\":1,\"drainedQpc\":2}";
   EventTap.Persisted(raw,"{\"queueSequence\":"+(i+1)+",\"pid\":100,\"kind\":"+AuthoritativeEvents.Quote(row.kind)+",\"persistedQpc\":3,\"removed\":true}");completed++;
  }
  double producer=w.Elapsed.TotalSeconds;EventTap.Finish();double all=w.Elapsed.TotalSeconds;
  var summary="{\"capacityOnly\":true,\"actualEventTapImplementation\":true,\"realWindowsEvents\":false,\"actualQueueDrainExercised\":false,\"requestedEvents\":"+events+",\"completedEvents\":"+completed+",\"authoritativeRecords\":"+(completed*3)+",\"producerSeconds\":"+producer.ToString("R",System.Globalization.CultureInfo.InvariantCulture)+",\"totalSeconds\":"+all.ToString("R",System.Globalization.CultureInfo.InvariantCulture)+",\"recordsPerSecond\":"+(completed*3/producer).ToString("R",System.Globalization.CultureInfo.InvariantCulture)+",\"tapRows\":"+EventTap.Snapshot().Length+",\"truncated\":"+EventTap.Truncated+",\"fault\":"+AuthoritativeEvents.Quote(EventTap.StreamFailure)+"}";
  Save(Path.Combine(root,"generated-load.json"),summary);return summary;
 }
}
