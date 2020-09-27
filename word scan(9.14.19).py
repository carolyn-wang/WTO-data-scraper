"""
need to code:
    try catch exception if format of input is mistyped
    exception if no text in pdf
U.S. - Cotton Subsidies (Panel) (21.5) 2007 ^0

Changes:
- filter()

this program is capable of printing: length of Findings, Findings starting page,
Conclusions starting page (Findings end page), total number of pages, PDF creation
date, title, author

panel reports link: http://worldtradelaw.net/databases/wtopanels.php
"""

import PyPDF2
import requests
import textract
import nltk
import re
import csv

from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

def getNextNum(list,index): #finds next int in document, following a given index
    index += 1
    found = False
    while found == False:
        if(list[index].isdigit()):
            found = True
            return list[index]
        else:
            index += 1

def getProgramVer(pdfReader):
    """
    verA: 2013 - now
    verB: 2003 - 2012
    verC: 1996 - 2003
    """
    date = pdfReader.getDocumentInfo()['/CreationDate'] #getting creation date of pdf
    year = (int)(date[2:6])
    if(year >= 2013):
        return 'verA'
    elif(year >= 2003):
        return 'verB'
    elif(year >= 1996):
        return 'verC'

def tokenizepdf(total_pgs, pdfReader):
    if(pdfReader.numPages < total_pgs):
        total_pgs = pdfReader.numPages
    cur_page = 1 #cur_page tracks current page being scanned
    text = ""

    while cur_page < total_pgs:
        pageObj = pdfReader.getPage(cur_page)
        cur_page += 1
        text += pageObj.extractText() # text variable contains all words scanned from pdf
 
    #cleaning text
    tokens = word_tokenize(text)
    unwanted = ['(',')',';',':','[',']',',', '...', '..','.', '-']
    stop_words = stopwords.words('english') #stop_words variable is articles (a, I, am, etc.)
    keywords = [word for word in tokens if not word in stop_words and not word in unwanted] #returns a list of words not in stop_words and not in punctuations

    return keywords

def getFindingsPgs(file_url):
    r = requests.get(file_url, stream = True)    
    
    with open("wtofile.pdf","wb") as pdf: 
        for chunk in r.iter_content(chunk_size=1024): 
            if chunk: # writing one chunk at a time to pdf file 
                pdf.write(chunk) 

    pdfFileObj = open("wtofile.pdf", 'rb') 
    pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
    total_pages = pdfReader.numPages
    
    
    numWord = 0 
    findingsPg = -1
    conclusionPg = -1
    cur_page = 1
    
    
    if(getProgramVer(pdfReader) == 'verA'):
        keywords = tokenizepdf(34, pdfReader)
        while numWord < len(keywords):
            if(keywords[numWord] == 'FINDINGS' and findingsPg == -1):
                if((keywords[numWord - 1]).isdigit()): # if keyword follows a number
                    findingsPg = getNextNum(keywords,numWord)
                    #print('Findings: ' + (str)(findingsPg))

            elif (keywords[numWord] == 'CONCLUSIONS' and conclusionPg == -1):
                if((keywords[numWord - 1]).isdigit()):
                    conclusionPg = getNextNum(keywords,numWord)
                    #print('Conclusion: ' + (str)(conclusionPg))
            numWord += 1
        cur_page += 1            

    elif(getProgramVer(pdfReader) == 'verB'):
        keywords = tokenizepdf(34, pdfReader)
        while numWord < len(keywords):
            if(keywords[numWord] == 'FINDINGS' and findingsPg == -1):
                if((keywords[numWord - 1]) == 'VII'):
                    findingsPg = getNextNum(keywords,numWord)
                    

            elif (keywords[numWord] == 'CONCLUSIONS' and conclusionPg == -1):
                if((keywords[numWord - 1]) == 'VIII'):
                    conclusionPg = getNextNum(keywords,numWord)
                    print(conclusionPg)
            numWord += 1
        cur_page += 1


    elif(getProgramVer(pdfReader) == 'verC'):
        while (findingsPg != -1 or conclusionPg != -1) and cur_page < total_pages:
            keywords = tokenizeNextPg(cur_page, pdfReader)
            cur_page += 1
            
            while numWord < len(keywords):
                if(keywords[numWord] == 'FINDINGS' and findingsPg == -1):
                    if((keywords[numWord - 1]) == 'VII' or (keywords[numWord - 1]) == 'VI' ):
                        findingsPg = cur_page

                elif (keywords[numWord] == 'CONCLUSIONS' and conclusionPg == -1):
                    if((keywords[numWord - 1]) == 'VIII' or (keywords[numWord - 1]) == 'VII'):
                        conclusionPg = cur_page
                numWord += 1


    pgCount = (int)(conclusionPg) - (int)(findingsPg)

    if (pgCount == -2):
        pgCount = 0

    return pgCount
    #print((str)(pdfReader.getDocumentInfo().title) + " " + pdfReader.getDocumentInfo()['/CreationDate'][2:6] + " ^" + (str)(pgCount))
    pdfFileObj.close()

##def tokenizeNextPg(pagenum, pdfReader):
##    text = ""
##    pageObj = pdfReader.getPage(pagenum)
##    text += pageObj.extractText() # text variable contains all words scanned from pdf
## 
##    tokens = word_tokenize(text)
##    unwanted = ['(',')',';',':','[',']',',', '...', '..','.', '-']
##    stop_words = stopwords.words('english') #stop_words variable is articles (a, I, am, etc.)
##    keywords_list = [word for word in tokens if not word in stop_words and not word in unwanted] #returns a list of words not in stop_words and not in punctuations
##    
##    return keywords_list
##
##def finished():
##    if (findingsPg != -1 and conclusionPg != -1):
##        return True
##    return False    
    

linksList = [] #list of urls from webpage

source = requests.get('http://www.worldtradelaw.net/databases/wtopanels.php/')
links = source.text.split('{"DecisionURL":"')## uses {"DecisionURL":" as divider
del links[0]
csv_file = open('cms_scrape.csv', 'w')
csv_writer = csv.writer(csv_file)
csv_writer.writerow(['Title','http link'])


for link in list(links):
    ## link = links[0]
    address = link.split('"Decision"')
    txt_http = re.sub(r"\\", "", address[0])
    txt_http = re.sub("pdf\",$", "pdf", txt_http)
    txt_http = txt_http.replace('pdf','pdf.download')
    txt = address[1].split('","FullDecisionURL":')
    txt_title = re.sub("^:\"", "", txt[0])
    findingsNum = getFindingsPgs(txt_http)
    print(txt_title, findingsNum)
    #print(txt_title, txt_http)
    csv_writer.writerow([txt_title, txt_http])
csv_file.close()


    


