from flask import Flask , render_template , request , redirect , url_for , session
from werkzeug import secure_filename
from google.cloud import vision
from PIL import Image
import io
import cloudinary
import cloudinary.api
import cloudinary.uploader
import requests
import json
import os

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
home = os.path.expanduser('~')
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(home , 'Downloads/auth-key.json')

dom_mapper = {
    'Button':'<button style="width:100%;height:100%;" type="button" class="btn btn-info">{}</button>',
    'CheckBox':'<input type="checkbox" name="test-box" value="test" style="width:50%;height:50%;" class="form-control" aria-describedby="basic-addon1"> {}<br>',
    'ComboBox':'<select><option value="test" style="width:100%;height:100%;">artificial option</option></select>',
    'Heading':'<h1>{}</h1>',
    'Image':'<img src="static/sample.jpg" style="max-width:100%;max-height:100%;" alt="AI Image">',
    'Label':'<label class="font-weight-bold">{}</label>',
    'Link':'',
    'Paragraph':'<p class="text-justify">Artificial paragraph....shasajnfafjfo safjajsn ahsf aushf asuihf aisfh asufaisf aif iasuhf iaushf asiufhaisufha faushfiausfha auhfiaus</p>',
    'RadioButton':'<input type="radio" name="AI" value="test" style="width:100%;height:100%;" class="form-control" aria-describedby="basic-addon1"> {}<br>',
    'TextBox':'<input type="text" name="test" style="width:100%;height:100%;" class="form-control" aria-describedby="basic-addon1"><br>'
}

element_annoter = 0

cloudinary.config( 
  cloud_name = "webvision", 
  api_key = "968156139689816", 
  api_secret = "JG9zEdCNyOyheg_GsVx75XRHODw" 
)

text_mapper = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate' , methods=['POST' , 'GET'])
def generate():
    styles = '<style>.test{position: fixed;overflow:hidden;}'
    image_url = "https://sketch2code.azurewebsites.net/Content/img/sampleDesigns/sample2.jpg"
    if request.method == 'POST':
        image_url = request.form['url']
        image_file = request.files['file']
        if image_url == '' and image_file.filename == '':
            return '<h1>Error - No data passed</h1>'
        if image_url == '' and image_file.filename != '':
            image_file.save(secure_filename(image_file.filename))
            cloudinary.api.delete_all_resources()
            result = cloudinary.uploader.upload_image(image_file.filename)
            image_url = result.url
            session['public-id'] = result.public_id
            os.remove(os.getcwd() + '/' + image_file.filename)

    json_headers = {
        'Content-Type':'application/json',
        'Prediction-Key':'467bb7cbcc1f4f0cb7a97895f0029b80',
    }

    data = {
        "Url": image_url,
    }

    res = requests.post('https://westus2.api.cognitive.microsoft.com/customvision/v3.0/Prediction/ddfbbef3-9278-4ff4-86a8-ffafaa38893f/detect/iterations/web-vision-v3/url' , data=json.dumps(data) , headers=json_headers)

    session['url'] = image_url
    predictions = json.loads(res.text)['predictions']

    valid_predictions = [prediction for prediction in predictions if prediction['probability'] > 0.15]

    print(len(valid_predictions))
    response = requests.get(image_url)
    img = Image.open(io.BytesIO(response.content))
    client = vision.ImageAnnotatorClient()
    for pred in valid_predictions:
        left = pred['boundingBox']['left']
        top = pred['boundingBox']['top']
        width = pred['boundingBox']['width']
        height = pred['boundingBox']['height']
        inter = 'left:{}%;top:{}%;width:{}%;height:{}%;'.format(left*100 , top*100 , width*100 , height*100)
        x = '#element-'+str(valid_predictions.index(pred))+'{' + inter + '}'
        styles = styles + x

        if pred['tagName'] == "Heading" or pred['tagName'] == "Label" or pred['tagName'] == "Button" or pred['tagName'] == "CheckBox" or pred['tagName'] == 'RadioButton':
            tag_feature = dom_mapper[pred['tagName']]
            t_width , t_height = img.size
            i_left = t_width*left
            i_right = t_height*top
            i_height = t_height*height
            i_width = t_width*width
            img_temp = img.crop((i_left , i_right , i_left + i_width , i_right + i_height))
            img_temp.save('slices/#element-'+str(valid_predictions.index(pred))+'.png' , "PNG")
            with io.open('slices/#element-'+str(valid_predictions.index(pred))+'.png', 'rb') as image_file:
                content = image_file.read()
            image = vision.types.Image(content=content)
            response = client.document_text_detection(image=image)
            new_text = response.text_annotations[0].description[:-1] if len(response.text_annotations) > 0 else 'Unrecognized Text'
            # dom_mapper[pred['tagName']] = tag_feature[:tag_feature.index('>')+1] + new_text + tag_feature[tag_feature[1:].index('<')+1:]
            text_mapper['element-'+str(valid_predictions.index(pred))] = new_text
    styles = styles + '</style>'
    print(styles)
    generated_code = render_template('test.html' , predictions=valid_predictions , dom=dom_mapper , style=styles , text=text_mapper)
    ptr = open('templates/generated/generated_template.html' , 'w')
    ptr.write(generated_code)
    ptr.close()
    print('File Generated')
    return redirect(url_for('result'))

@app.route('/generated_template')
def generate_template():
    return render_template('generated/generated_template.html')

@app.route('/result')
def result():
    return render_template('result.html' , url=session['url'])


if __name__ == '__main__':
    app.run(debug=True)