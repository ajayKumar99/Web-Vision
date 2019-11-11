from azure.cognitiveservices.vision.customvision.training import CustomVisionTrainingClient
from azure.cognitiveservices.vision.customvision.training.models import ImageFileCreateEntry , Region
import os
import json

training_key = "467bb7cbcc1f4f0cb7a97895f0029b80"
ENDPOINT = "https://westus2.api.cognitive.microsoft.com/"

trainAPI = CustomVisionTrainingClient(training_key , ENDPOINT)

domains = trainAPI.get_domains()
project = trainAPI.get_projects()[0]

modelPath = os.getcwd() + '/model'
dataPath = os.path.join(modelPath , 'dataset.json')
imagesPath = os.path.join(modelPath , 'images')
print(modelPath , dataPath , imagesPath)

file = open(dataPath)
images = json.loads(file.read())
file.close()

print(project)
existingTags = trainAPI.get_tags(project_id=project.id)

# for tag in existingTags:
#     trainAPI.delete_tag(project.id , tag.id)

tag_flag = 0
if len(existingTags) == 0:
    tag_flag = 1

if tag_flag == 1:
    tagstoimport = {}

    for image in images:
        for tag in image['tags']:
            tagstoimport[tag['tagName']] = tag

    print(tagstoimport)

    for tag in tagstoimport.keys():
        print("Importing tag - " , tag)
        newTag = trainAPI.create_tag(project.id , tag)
        existingTags.append(tag)

tagtoidmapper = {}

for tag in existingTags:
    tagtoidmapper[tag.name] = tag.id

print(tagtoidmapper)

tagged_images_with_regions = []
z = 1

for image in images:

    if z%50 == 0:
        upload_result = trainAPI.create_images_from_files(project.id , images=tagged_images_with_regions)
        tagged_images_with_regions = []
    regions = []

    for region in image['regions']:
        regions.append(Region(tag_id=tagtoidmapper[region['tagName']] , left=region['left'] , top=region['top'] , width=region['width'] , height=region['height']))
    image_file = open(os.path.join(imagesPath , image['id']+'.png') , 'rb')
    tagged_images_with_regions.append(ImageFileCreateEntry(name=image['id'] , contents=image_file.read() , regions=regions))
    image_file.close()
    z = z + 1

upload_result = trainAPI.create_images_from_files(project.id , images=tagged_images_with_regions)
