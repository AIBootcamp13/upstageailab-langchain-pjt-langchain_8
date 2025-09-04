# src/vision_processor.py
from pathlib import Path
from transformers import pipeline
from PIL import Image

def describe_image(image_path: Path, model_name: str) -> str:
    """
    이미지 파일 경로와 모델 이름을 받아 이미지에 대한 텍스트 설명을 생성합니다.

    Args:
        image_path (Path): 처리할 이미지 파일의 경로.
        model_name (str): 사용할 Hugging Face 모델의 이름.

    Returns:
        str: 이미지에서 추출된 텍스트 설명.
    """
    try:
        # 'image-to-text' 파이프라인을 사용하여 이미지 캡셔닝 모델을 로드합니다.
        # 이 파이프라인은 초기화 시 모델을 다운로드합니다.
        captioner = pipeline("image-to-text", model=model_name)

        # Pillow를 사용하여 이미지 파일을 엽니다.
        img = Image.open(image_path)

        # 모델을 사용하여 설명을 생성합니다.
        # 결과는 일반적으로 [{'generated_text': '...'}] 형식의 리스트입니다.
        results = captioner(img)
        description = results[0].get('generated_text', '')

        return f"Image content description: {description}"
    except Exception as e:
        # 오류 발생 시, 간단한 오류 메시지를 반환합니다.
        print(f"Error processing image {image_path}: {e}")
        return "Could not describe the image."