import os
import uuid
from typing import Annotated
from fastapi import APIRouter, Request, Depends, File, UploadFile
from datetime import datetime

from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from fastapi.templating import Jinja2Templates
from src.database import get_db
from .audio_utils import *
from src.models import Audio


templates = Jinja2Templates(directory="templates")

router = APIRouter(tags=["audio"])
vad = WebRTCVAD()

MEDIA_DIR = "media/"
ORIGINAL_AUDIO_DIR  = "media/original/"
PROCESSED_AUDIO_DIR = "media/processed/"


@router.get("/", name="index")
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "audio_data": None})


@router.post("/")
async def post_index(request:       Request,
               original_audio_file: Annotated[None | UploadFile, File()],
               # original_text:       None | str,
               db:                  Annotated[Session, Depends(get_db)]):
    create_date = datetime.now()
    # 폼에서 받아온 original_audio 저장
    filepath = f"{MEDIA_DIR}{original_audio_file.filename}"
    data = await original_audio_file.read()
    with open(filepath, "wb") as f:
        f.write(data)

    # audio, text input
    # for문 original_audio(조각), processed_audio, processed_text, onset, offset
    # 받아 새 모델 생성 후 add
    num_audios, onsets, offsets, _, wav_audios = vad.detect_endpoints(filepath)
    texts = SpeechRecognition().recognize_korean(num_audios=num_audios)
    audio_data = []
    for i in range(num_audios):
        unique_id = str(uuid.uuid4())
        original_filepath = ORIGINAL_AUDIO_DIR + unique_id
        processed_filepath = PROCESSED_AUDIO_DIR + unique_id

        kr_text = texts[i]
        en_text = text_translate(kr_text)
        tts_file = text_to_tts(en_text)

        new_audio = Audio(create_date           = create_date,
                          original_audio_path   = original_filepath,
                          original_text         = kr_text,
                          processed_audio_path  = processed_filepath,
                          processed_text        = en_text,
                          onset                 = onsets[i],
                          offset                = offsets[i]
                          )

        # dir에 오리지널, 프로세스 파일 저장
        with open(original_filepath, "wb") as f:
            f.write(wav_audios[i].getvalue())

        with open(processed_filepath, "wb") as f:
            f.write(tts_file.getvalue())

        audio_data.append(new_audio)
    # media에 저장한 원본 파일 지우기
    os.remove(filepath)

    db.add_all(audio_data)
    db.commit()
    return templates.TemplateResponse("index.html", {"request": request, "audio_data": audio_data})