# src/vision_processor.py

import torch
from pathlib import Path
from transformers import pipeline
from PIL import Image

def describe_image(image_path: Path, model_name: str) -> str:
    """
    이미지 파일 경로와 모델 이름을 받아 이미지에 대한 텍스트 설명을 생성합니다.
    LLaVA 모델은 이미지와 텍스트 프롬프트가 모두 필요합니다.
    """
    try:
        # LLaVA와 같은 복잡한 모델을 위해 파이프라인을 더 명시적으로 설정합니다.
        # torch_dtype을 사용하여 메모리 사용량을 최적화하고 GPU를 지정합니다.
        captioner = pipeline(
            "image-to-text",
            model=model_name,
            torch_dtype=torch.float16,
            device=0  # 첫 번째 GPU 사용
        )

        img = Image.open(image_path).convert("RGB")

        # LLaVA 모델이 작동하려면 텍스트 프롬프트가 필요합니다.
        # 파이프라인은 이 프롬프트를 내부적으로 모델의 템플릿에 맞게 포맷팅합니다.
        prompt = "USER: <image>\nWhat is a detailed description of this image?\nASSISTANT:"

        # 파이프라인을 호출할 때 이미지와 프롬프트를 모두 전달합니다.
        # max_new_tokens를 설정하여 응답 길이를 제어할 수 있습니다.
        results = captioner(images=img, prompt=prompt, generate_kwargs={"max_new_tokens": 512})
        
        description = results[0].get('generated_text', '')

        # 응답에서 프롬프트를 제거하여 순수한 설명만 남깁니다.
        # LLaVA 모델은 종종 입력 프롬프트를 결과에 포함합니다.
        if "ASSISTANT:" in description:
            description = description.split("ASSISTANT:")[-1].strip()

        return f"Image content description: {description}"
    except Exception as e:
        print(f"Error processing image {image_path}: {e}")
        return "Could not describe the image."