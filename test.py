from google.cloud import vision
import os
from PIL import Image
import requests
from io import BytesIO
import io

# response = requests.get('https://res.cloudinary.com/webvision/image/upload/v1572942518/wyebxchmo9xz0coost6w.jpg')
# img = Image.open(BytesIO(response.content))
# img = img.crop((130, 120, 200, 200))
# img.save("sampler.png" , "PNG")

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "service-account-file.json"

client = vision.ImageAnnotatorClient()
# image = vision.types.Image()
# image.source.image_uri = 'https://res.cloudinary.com/webvision/image/upload/v1572973296/tester_bjyjye.png'

# response = client.document_text_detection(image=image)

# print(response.text_annotations[0].description[:-1])

with io.open('slices/#element-2.png', 'rb') as image_file:
    content = image_file.read()
image = vision.types.Image(content=content)
response = client.document_text_detection(image=image)
print(len(response.text_annotations))