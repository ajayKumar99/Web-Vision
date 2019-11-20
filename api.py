from flask import Flask , render_template , request , redirect , url_for , session , send_file
from werkzeug import secure_filename
from google.cloud import vision
import cloudinary
import cloudinary.api
import cloudinary.uploader

from PIL import Image
import io
import requests
import json
import os

app = Flask(__name__)
home = os.path.expanduser('~')
auth_file = 'Downloads/.flask_key'
ptr = open(os.path.join(home , auth_file), 'r')
app.secret_key = ptr.read()
ptr.close()

vision_auth_file = 'Downloads/vision-auth.json'
ptr = open(os.path.join(home , vision_auth_file) , 'r')
vision_auth = json.loads(ptr.read())
ptr.close()

prediction_key = vision_auth['training_key']
ENDPOINT = vision_auth['ENDPOINT']

dom_mapper = {
    'Button':'<button style="width:100%;height:100%;" type="button" class="btn btn-info">{}</button>',
    'CheckBox':'<input type="checkbox" name="test-box" value="test" style="width:50%;height:50%;" class="form-control" aria-describedby="basic-addon1"> {}<br>',
    'ComboBox':'<div class="dropdown"><button class="btn btn-secondary dropdown-toggle" type="button" id="dropdownMenuButton" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">{}</button><div class="dropdown-menu" aria-labelledby="dropdownMenuButton"><a class="dropdown-item" href="#">Action</a></div></div>',
    'Heading':'<h1>{}</h1>',
    'Image':'<img src="static/sample.jpg" style="max-width:100%;max-height:100%;" alt="{}">',
    'Label':'<label class="font-weight-bold">{}</label>',
    'Link':'<a href="#"><!--{}--></a>',
    'Paragraph':'<p class="text-justify">Artificial paragraph {} hasajnfafjfo safjajsn ahsf aushf asuihf aisfh asufaisf aif iasuhf iaushf asiufhaisufha faushfiausfha auhfiaus</p>',
    'RadioButton':'<input type="radio" name="AI" value="test" style="width:100%;height:100%;" class="form-control" aria-describedby="basic-addon1"> {}<br>',
    'TextBox':'<input type="text" name="test" style="width:100%;height:100%;" class="form-control" aria-describedby="basic-addon1"><br>'
}

text_mapper = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate/<api>' , methods=['POST' , 'GET'])
def generate(api):
    styles = '<style>.test{position: fixed;}'
    image_url = "https://sketch2code.azurewebsites.net/Content/img/sampleDesigns/sample2.jpg"
    if request.method == 'POST' and int(api) == 0:
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
    elif request.method == 'POST' and int(api) == 1:
        image_url = request.get_json()['url']

    json_headers = {
        'Content-Type':'application/json',
        'Prediction-Key':prediction_key
    }

    data = {
        "Url": image_url,
    }

    res = requests.post('https://westus2.api.cognitive.microsoft.com/customvision/v3.0/Prediction/ddfbbef3-9278-4ff4-86a8-ffafaa38893f/detect/iterations/Iteration5/url' , data=json.dumps(data) , headers=json_headers)

    session['url'] = image_url
    predictions = json.loads(res.text)['predictions']

    valid_predictions = [prediction for prediction in predictions if prediction['probability'] > 0.15]
    valid_predictions = sorted(valid_predictions , key = lambda k:k['probability'])
    print(len(valid_predictions))
    response = requests.get(image_url)
    img = Image.open(io.BytesIO(response.content))
    client = vision.ImageAnnotatorClient()
    for pred in valid_predictions:
        left = pred['boundingBox']['left']
        top = pred['boundingBox']['top']
        width = pred['boundingBox']['width']
        height = pred['boundingBox']['height']
        if pred['tagName'] == 'Heading' or pred['tagName'] == 'Label' or pred['tagName'] == 'Combobox':
            inter = 'left:{}%;top:{}%;width:{};height:{};'.format(left*100 , top*100 , 'auto' , 'auto')
        else:
            inter = 'left:{}%;top:{}%;width:{}%;height:{}%;'.format(left*100 , top*100 , width*100 , height*100)
        if pred['tagName'] == 'Heading' or pred['tagName'] == 'Label':
            inter = inter + 'min-height:fit-content;min-width:fit-content;'
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
    if int(api) == 1:
        return generated_code
    return redirect(url_for('result'))

@app.route('/generated_template')
def generate_template():
    return render_template('generated/generated_template.html')

@app.route('/download_document')
def download_document():
    return send_file('templates/generated/generated_template.html' , as_attachment=True , attachment_filename='output.html' , mimetype='application/download')

@app.route('/web_vision_toolkit')
def web_vision_toolkit():
    return render_template('toolkit.html')

@app.route('/result')
def result():
    #Delete slices
    for slice in os.listdir('slices/'):
        path = os.path.join('slices/' , slice)
        try:
            if os.path.isfile(path):
                os.unlink(path)
        except Exception as e:
            pass
    return render_template('result.html' , url=session['url'])


if __name__ == '__main__':

    #Google Authentication 
    auth_file_location = 'Downloads/auth-key.json'  #Replace with your auth file location
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(home , auth_file_location)

    #Cloudinary Authentication
    cloudinary_auth_file = 'Downloads/cloudinary-auth.json' #Replace with your auth file location
    ptr = open(os.path.join(home , cloudinary_auth_file) , 'r')
    cloudinary_auth = json.loads(ptr.read())
    ptr.close()
    cloudinary.config( 
    cloud_name = cloudinary_auth['cloud_name'], 
    api_key = cloudinary_auth['api_key'], 
    api_secret = cloudinary_auth['api_secret'] 
    )

    #Slices folder for OCR
    if not os.path.isdir('slices'):
        os.mkdir('slices')

    app.run(debug=True)