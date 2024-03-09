import csv
import json
import zipfile
import io
from flask import Flask, request, send_file, make_response, send_from_directory
import os
from uuid import uuid4
from distutils.dir_util import copy_tree
import shutil

SD_PROFILE_NAME = '412EC73E-6405-41E9-8AEC-8240F5E43C40.sdProfile'
APP_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
LETTERS = ['A','B','C','D']
INTERVALS = [
    (i*14+1,i*14+14)
    for i in range(13)
]

def find_letter_interval(d):
    
    for controller in d['Controllers']:
        for position, action in controller['Actions'].items():
            for state in action['States']:    
                if 'Title' not in state:
                    continue
                for letter in LETTERS:
                    for interval in INTERVALS:
                        if state['Title'] == letter + str(interval[0]):
                            return letter, interval
                        
    return None, None

PROFILES = { letter: {} for letter in LETTERS }

for fname in os.listdir(APP_DIRECTORY + '/' + SD_PROFILE_NAME + '/' + 'Profiles'):

    with open(APP_DIRECTORY + '/' + SD_PROFILE_NAME + '/' + 'Profiles' + '/' + fname + '/' + 'manifest.json') as f:
        
        d = json.load(f)
        letter, interval = find_letter_interval(d)

        if letter is None or interval is None:
            continue
                          
        PROFILES[letter][interval] = fname

# print(PROFILES)

app = Flask(__name__)

def modify_json(d, letter, number, name, url):

    selected_action = None

    for controller in d['Controllers']:
        for position, action in controller['Actions'].items():
            for state in action['States']: 
                if state.get('Title') == letter + str(number):
                    selected_action = action
                    break
            if selected_action:
                break
        if selected_action:
            break

    for a in selected_action['Actions']:
        if 'Actions' not in a:
            continue
        for b in a['Actions']:
            if 'Settings' not in b:
                continue
            if 'sourceURL' in b['Settings']:
                b['Settings']['sourceURL'] = url
            if 'imageFileName' in b['Settings']:
                parts = b['Settings']['imageFileName'].split('Afro')
                b['Settings']['imageFileName'] = parts[0] + name + parts[1]


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Get the uploaded CSV file from the form data
        csv_file = request.files['csv_file']
        data = {}
        data['items'] = []

        with io.TextIOWrapper(csv_file) as fh:

          # Specify the correct encoding when parsing the CSV file
          reader = csv.DictReader(fh)

          # Parse the CSV file into a dictionary where keys are header row values and values are lists of corresponding cell values
          
          for row in reader:
              data['items'].append(row)

        # print(data)
              
        tmp_directory = '/tmp/' + str(uuid4())

        os.makedirs(tmp_directory)
        copy_tree(APP_DIRECTORY + '/' + SD_PROFILE_NAME, tmp_directory + '/' + SD_PROFILE_NAME)

        for player in data['items']:

            # print(player)

            interval = INTERVALS[(int(player['number']) - 1) // 14]

            for letter in LETTERS:

                profile = PROFILES[letter][interval]
                file_path = tmp_directory + '/' + SD_PROFILE_NAME + '/' + 'Profiles' + '/' + profile + '/' + 'manifest.json'

                d = None

                with open(file_path, "r") as f:
                    d = json.load(f)

                modify_json(d, letter, player['number'], player['name'], player['url'])

                with open(file_path, "w") as f:
                    json.dump(d, f)


        memory_file = io.BytesIO()
        file_path = tmp_directory + '/' + SD_PROFILE_NAME + '/'
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(file_path):
                for file in files:
                    zipf.write(os.path.join(root, file), arcname=os.path.join(root.removeprefix(tmp_directory + '/'),file))
                # include empty dirs
                for dir in dirs:
                    if os.listdir(os.path.join(root, dir)) == []:
                        zif = zipfile.ZipInfo(os.path.join(root, dir).removeprefix(tmp_directory + '/') + "/")  
                        zipf.writestr(zif, "")  


        memory_file.seek(0)

        return send_file(memory_file,
                        download_name=SD_PROFILE_NAME + '.zip',
                        as_attachment=True)

    else:
        # Display a simple HTML form allowing file uploads
        html = '''
        <html>
          <body>
            <form action="/" method="post" enctype="multipart/form-data">
              Select a CSV file:

              <input type="file" name="csv_file">

              <input type="submit" value="Process File">
            </form>
            Example CSV file :<br>
            <br>
            number,name,url<br>
            1,Baruch,https://www.twitch.tv/baruchetmoi<br>
            2,Seijouf,https://www.twitch.tv/seijouf<br>
            <br>
            You can create a CSV file from a Google Sheet : File > Download > Comma Separated Values (.csv)<br>
          </body>
        </html>
        '''
        return html

if __name__ == "__main__":
    app.run(debug=True)