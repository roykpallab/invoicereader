from wand.image import Image
from PIL import Image as PI
import pyocr
import pyocr.builders
import io
from fuzzywuzzy import process,fuzz
from glob import glob
import numpy as np
import shutil


REF_COM_KEY=['Xtra Aged Care', 'Yarra Valley Farms','Unknown']
REF_INVOICE_KEY=['Invoice Number','Document']
REF_DATE_KEY=['Date']
REF_MONTH_NAME_KEY=['Jan', 'Feb', 'Mar','Apr']
SIM_THS=70


# convert a scanned pdf into text
# input: path of the pdf file
# output: list of string
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
            # print word.content
    return words

#Return find similarity score with respect to each line in a sentence
#input: reference key word, list of document
#output: line number having max similarity with the keyword, all similarity scores
def find_line_number_ref_word(ref_word,words):
    similariy_score=[]
    for word in words:
        similariy_score.append(fuzz.partial_ratio(ref_word,word))
    return similariy_score.index(max(similariy_score)),similariy_score

#check whether a string contain a number or not
#input: string
#output: boolean
def hasNumbers(inputString):
    return any(char.isdigit() for char in inputString)


#find the index of reference key word in a line
#input: reference keyword, line
#output:position of the key word in the line, position of the keyword in the keyword list
def compare_line_ref_keywords(ref_keywordlist,line):
    words_line=line.split(' ')
    similarity_score=[]
    sim_word_index=[]
    for key in ref_keywordlist:
        sub_similarity_score=[]
        for word_line in words_line:
            sub_similarity_score.append(fuzz.partial_ratio(key,word_line))
        similarity_score.append(max(sub_similarity_score))
        sim_word_index.append(sub_similarity_score.index(max(sub_similarity_score)))

    max_similariy_score=max(similarity_score)
    max_sim_key_index=similarity_score.index(max(similarity_score))
    sim_key_position=sim_word_index[max_sim_key_index]
    if max_similariy_score>SIM_THS:
        return sim_key_position,max_sim_key_index
    else:
        return np.inf,np.inf

#find digit in a string
#input:string
#output:char of the digit
def find_digit(string):
    for s in string:
        if (s.isdigit()):
            return s


#find date using month key
def find_date_format_one(month_position,month_key,ref_line):
    ref_line_words=ref_line.split(' ')
    dd=ref_line_words[month_position-1]
    mm='0'+str(month_key+1)
    year= ref_line_words[month_position+1][2:]
    return dd+mm+year

#find date when there is no month key
def find_date_format_two(date_position,ref_line):
    ref_line_words=ref_line.split(' ')
    ref_date_word=ref_line_words[date_position+1]
    dd=ref_date_word[:2]
    mm=ref_date_word[3:5]
    year=ref_date_word[8:]
    return dd+mm+year


#find company name in the scanned document
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

#find invoice number in the scanned document
def find_invoice_number(ref_inv_key,words):
    line_number,_=find_line_number_ref_word(ref_inv_key,words)
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

# find invoice date in the scanned document
def find_invoice_date(ref_date_key,words):
    line_number,_=find_line_number_ref_word(ref_date_key,words)
    if hasNumbers(words[line_number]):
        ref_line=words[line_number]
        key=compare_line_ref_keywords(REF_DATE_KEY,ref_line)
        date=find_date_format_two(key[0],ref_line)
    else:
        ref_line=words[line_number+1]
        key=compare_line_ref_keywords(REF_MONTH_NAME_KEY,ref_line)
        date=find_date_format_one(key[0],key[1],ref_line)
    return date


def estimate_invoice_name(input_dir,output_dir):
    files=glob(input_dir)
    for id,path in enumerate(files):
        file_name=path.split('/')[-1]
        file_name=file_name.split('.')[0]
        file_id=find_digit(file_name)
        words=convert_pdf_string(path)
        comp_indx=find_company(words)
        comp_name=REF_COM_KEY[comp_indx]
        if comp_name==REF_COM_KEY[-1]:
            pred_path=output_dir+file_name+'-'+comp_name+'-'+file_id+'.pdf'
        else:
            invoice_number=find_invoice_number(REF_INVOICE_KEY[comp_indx],words)
            date=find_invoice_date(REF_DATE_KEY[0],words)
            pred_path=output_dir+file_name+'-'+comp_name+'-'+invoice_number+'-'+date+'.pdf'
        print('Copy to'+pred_path)
        shutil.copy(path,pred_path)






