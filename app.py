import os
import time
import requests
from selenium import webdriver

from flask_cors import CORS,cross_origin
from flask import Flask, render_template, request,jsonify

# import request
app = Flask(__name__) # initialising the flask app with the name 'app'
@app.route('/')  # route for redirecting to the home page
def home():
    return render_template('index.html')

def fetch_image_urls(query: str, max_links_to_fetch: int, wd: webdriver, sleep_between_interactions: int = 1):
    def scroll_to_end(wd):
        wd.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(sleep_between_interactions)

        # build the google query

    search_url = "https://www.google.com/search?safe=off&site=&tbm=isch&source=hp&q={q}&oq={q}&gs_l=img"

    # load the page
    wd.get(search_url.format(q=query))

    image_urls = set()
    image_count = 0
    results_start = 0
    while image_count < max_links_to_fetch:
        scroll_to_end(wd)

        # get all image thumbnail results
        thumbnail_results = wd.find_elements_by_css_selector("img.Q4LuWd")
        number_results = len(thumbnail_results)

        print(f"Found: {number_results} search results. Extracting links from {results_start}:{number_results}")

        for img in thumbnail_results[results_start:number_results]:
            # try to click every thumbnail such that we can get the real image behind it
            try:
                img.click()
                time.sleep(sleep_between_interactions)
            except Exception:
                continue

            # extract image urls
            actual_images = wd.find_elements_by_css_selector('img.n3VNCb')
            for actual_image in actual_images:
                if actual_image.get_attribute('src') and 'http' in actual_image.get_attribute('src'):
                    image_urls.add(actual_image.get_attribute('src'))

            image_count = len(image_urls)

            if len(image_urls) >= max_links_to_fetch:
                print(f"Found: {len(image_urls)} image links, done!")
                break
        else:
            print("Found:", len(image_urls), "image links, looking for more ...")
            time.sleep(30)
            return
            load_more_button = wd.find_element_by_css_selector(".mye4qd")
            if load_more_button:
                wd.execute_script("document.querySelector('.mye4qd').click();")

        # move the result startpoint further down
        results_start = len(thumbnail_results)

    return image_urls

def persist_image(folder_path:str,url:str, counter):
    try:
        image_content = requests.get(url).content

    except Exception as e:
        print(f"ERROR - Could not download {url} - {e}")

    try:
        f = open(os.path.join(folder_path, 'jpg' + "_" + str(counter) + ".jpg"), 'wb')
        f.write(image_content)
        f.close()
        print(f"SUCCESS - saved {url} - as {folder_path}")
    except Exception as e:
        print(f"ERROR - Could not save {url} - {e}")

def search_and_download(search_term: str, target_path='./static', number_images=4):
    target_folder = os.path.join(target_path, '_'.join(search_term.lower().split(' '))) # make the folder name inside images with the search string

    if not os.path.exists(target_folder):
        os.makedirs(target_folder) # make directory using the target path if it doesn't exist already

    chrome_options = webdriver.ChromeOptions()
    chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")

    with webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=chrome_options) as wd:
        res = fetch_image_urls(search_term, number_images, wd=wd, sleep_between_interactions=0.5)

    counter = 0
    for elem in res:
        persist_image(target_folder, elem, counter)
        counter += 1


@app.route('/searchImages', methods=['GET','POST'])
def searchImages():
   # list_of_images= os.listdir('./static')
    # for image in list_of_images:
    #         name_array = image.split('.')
    #         if (name_array[1] == 'jpg'):
    #             os.remove("./static/"+str+image)

    if request.method == 'POST':
        print("entered post")
        keyWord = request.form['keyword'] # assigning the value of the input keyword to the variable keyword

    else:
        print("did not enter post")
    print('printing = ' + keyWord)




  #  DRIVER_PATH = './chromedriver'
    search_term = keyWord
    # num of images you can pass it from here  by default it's 10 if you are not passing
    # number_images = 10
    search_and_download(search_term=search_term)

    list_of_files=[]
    #files=[]
    list_of_files = os.listdir('./static/'+keyWord)


    list_of_files = [keyWord+'/'+ image for image in list_of_files]
    # for file in list_of_files:
    #     name_array = file.split('.')
    #     if (name_array[1] == 'jpg'):
    #         files.append(file)

    print('list of files==')
    print(list_of_files)
    try:
        if(len(list_of_files)>0): # if there are images present, show them on a wen UI
            return render_template('gallery.html',list_of_files = list_of_files)
        else:
            return "Please try with a different string" # show this error message if no images are present in the static folder
    except Exception as e:
        print('no Images found ', e)
        return "Please try with a different string"


if __name__ == "__main__":
    #app.run(host='127.0.0.1', port=8000,debug=True)
    app.run(debug=True)
