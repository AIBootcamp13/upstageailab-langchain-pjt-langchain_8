# src/audio_processor.py
from pathlib import Path
from transformers import pipeline

def transcribe_audio(audio_path: Path, model_name: str) -> str:
    """
    오디오 파일 경로와 모델 이름을 받아 텍스트로 변환합니다.

    Args:
        audio_path (Path): 처리할 오디오 파일의 경로.
        model_name (str): 사용할 Hugging Face ASR 모델의 이름.

    Returns:
        str: 오디오에서 변환된 텍스트.
    """
    try:
        # 'automatic-speech-recognition' 파이프라인을 사용하여 ASR 모델을 로드합니다.
        transcriber = pipeline(
            "automatic-speech-recognition", 
            model=model_name, 
            device=0  # Use the first available GPU
)
        # 모델을 사용하여 오디오 파일을 텍스트로 변환합니다.
        # 긴 오디오의 경우 chunk_length_s를 설정하여 분할 처리할 수 있습니다.
        results = transcriber(str(audio_path), chunk_length_s=30)

        transcription = results.get('text', '')

        return f"Audio transcript: {transcription}"
    except Exception as e:
        # 오류 발생 시, 간단한 오류 메시지를 반환합니다.
        print(f"Error processing audio {audio_path}: {e}")
        return "Could not transcribe the audio."