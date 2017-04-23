from wand.image import Image
from PIL import Image as PI
import pyocr
import pyocr.builders
import io
from fuzzywuzzy import process
from fuzzywuzzy import fuzz
from glob import glob
REF_COM_KEY=['Xtra Aged Care', 'Yarra Valley Farms','Unknown']
REF_INVOICE_KEY=['Invoice Number','Document']
SIM_THS=70

def convert_pdf_string(path):
    tool = pyocr.get_available_tools()[0]
    req_image = []
    all_page_word_object=[]
    image_pdf = Image(filename=path, resolution=300)
    image_jpeg = image_pdf.convert('jpeg')
    for img in image_jpeg.sequence:
        img_page = Image(image=img)
        req_image.append(img_page.make_blob('jpeg'))
    for img in req_image:
        words_object= tool.image_to_string(PI.open(io.BytesIO(img)),
        lang="eng",
        builder=pyocr.builders.LineBoxBuilder())
        all_page_word_object.append(words_object)

    num_pages=len(all_page_word_object)
    first_page_word_object=all_page_word_object[num_pages-1]
    words=[]
    for word in first_page_word_object:
        if(word.content):
            words.append(word.content)
            #print word.content
    return words

def find_line_number_ref_word(ref_word,words):
    similariy_score=[]
    for word in words:
        similariy_score.append(fuzz.partial_ratio(ref_word,word))
    return similariy_score.index(max(similariy_score))


def hasNumbers(inputString):
    return any(char.isdigit() for char in inputString)

def find_company(words):
    comp_similary_score_list=[]
    for comp in REF_COM_KEY:
        comp_similary= process.extractOne(comp, words)
        comp_similary_score_list.append(comp_similary[1])
    max_comp_similarity_score=max(comp_similary_score_list)
    if max_comp_similarity_score>SIM_THS:
        return comp_similary_score_list.index(max(comp_similary_score_list))
    else:
        return len(REF_COM_KEY)-1

def find_invoice_number(ref_inv_key,words):
    line_number=find_line_number_ref_word(ref_inv_key,words)
    for i in range(line_number,line_number+5,1):
        if(hasNumbers(words[i])):
            find_date_prob=fuzz.partial_ratio('Date',words[i])
            find_phn_prob=fuzz.partial_ratio('P:',words[i])
            if find_phn_prob>SIM_THS:
                sub_word_list=words[i].split(' ')
                if(hasNumbers(sub_word_list[0])):
                   return sub_word_list[0]
            elif (find_date_prob>SIM_THS or find_phn_prob>SIM_THS):
                continue
            else:
                break

    splitted_line=words[i].split()
    for sub_word in splitted_line:
        if(hasNumbers(sub_word)):
            break

    return sub_word



if __name__=='__main__':

    files=glob("./input/*.pdf")
    for id,path in enumerate(files):
        # if id==3:
            words=convert_pdf_string(path)
            comp_indx=find_company(words)
            comp_name=REF_COM_KEY[comp_indx]
            if comp_name==REF_COM_KEY[-1]:
                invoice_number=path.split('invoice')[-1].split('.')[0]
            else:
                invoice_number=find_invoice_number(REF_INVOICE_KEY[comp_indx],words)

            print comp_name,invoice_number




