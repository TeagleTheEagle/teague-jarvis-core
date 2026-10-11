from dataclasses import dataclass
import os
from .contracts import WearableError


@dataclass(frozen=True)
class Config:
    ai: str='mock'
    voice: str='mock'
    mic: str='fixture'
    vision: str='mock'

    def validate(self):
        if self.ai not in ('mock','real') or self.voice not in ('mock','real') or self.mic not in ('fixture','live') or self.vision not in ('mock','real'):
            raise WearableError('INVALID_MODE')
        # Vision and answer generation use one existing Core turn, not two providers.
        if self.vision=='real' and self.ai!='real':raise WearableError('REAL_VISION_REQUIRES_REAL_AI')
        return self

    @classmethod
    def from_env(cls):
        return cls(os.getenv('AI_MODE','mock'),os.getenv('VOICE_MODE','mock'),os.getenv('MIC_MODE','fixture'),os.getenv('VISION_MODE','mock')).validate()
