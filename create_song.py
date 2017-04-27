#!/usr/bin/python
# -*- coding: utf-8 -*-

def convert(path, f, target=None):
    import re #für Regular Expressions (google es ;))
    from collections import OrderedDict #andernfalls würde sich Vers1, Chorus usw immer alphabetisch sortieren
    from pandas import read_csv, Index
    #alle Imports für die PDF Generierung (unbedingt für nächster Zelle mit pyth ausführen)
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import inch
    from reportlab.pdfbase.pdfmetrics import stringWidth
    from reportlab.lib import styles, colors
    from reportlab.platypus import Paragraph
    #RTF einlese Package
    from pyth.plugins.rtf15.reader import Rtf15Reader
    from pyth.plugins.plaintext.writer import PlaintextWriter
    #RTF einlesen
    doc = Rtf15Reader.read(f)
    raw = PlaintextWriter.write(doc).getvalue()
    pattern="(^[\xc3\x9f\xc3\x84\xc3\x96\xc3\x9c\xc3\xa4\xc3\xbc\xc3\xb6\w\s]+\n+)(key:[\w#]+\n+)?(bpm:[\d]+\n+)?(.+)(CCLI Song # (\d+)\\n+(.+)\\n+\\xc2\\xa9 (.+))"
    match = re.search(pattern,raw,re.DOTALL)
    info_dict = {}
    info_dict['title'] = match.group(1).replace('\n','')
    if match.group(2):
        info_dict['key'] = match.group(2).replace('\n','').replace('key:','')
    else:
        print "No key found"
    if match.group(3):
        info_dict['bpm'] = match.group(3).replace('\n','').replace('bpm:','')
    else:
        print "No bpm found"
    info_dict['song'] = match.group(4)
    info_dict['ccli_nr'] = match.group(6)
    info_dict['composer'] = match.group(7).replace('\n','')
    info_dict['copyright'] = match.group(8)
    akkorde = read_csv("Akkorde.csv",sep=";")
    def getTransformedKey (source, target, chord):
        return(akkorde[target][Index(akkorde[source]).get_loc(chord)])
    def replChords (matchObj):
        return ('['+getTransformedKey(source = info_dict['key'], target = target, chord = matchObj.group(1))+']')
    def transform():
        info_dict['song'] = re.sub('\[([\w\d#/]+)\]', replChords, info_dict['song'])
        info_dict['key'] = target
    #target = request.form['trans_key']
    if (target and target != info_dict['key']):
        transform()
    #Einzelne Zeilen aus dem RTF in Liste laden
    line_list = info_dict.get('song').split('\n\n')
    line_list
    pattern = '^(Verse\s?\d*|Chorus\s?\d*|Instrumental|Bridge|Pre-Chorus|Intro)$' #Dieses Pattern funktioniert auf alles VersX und Chorus in eckiger Klammer (porbier regexr.com)
    song_dict = OrderedDict() #Das oben erwähnte Ordered Dict
    in_element = False #mit diesem Flag könnte man sich später noch title: composer: key: usw holen (so weit bin ich noch nicht)
    element = None #hier wird gleich drin gespeichert, in welcher Untergruppe wir jeweils sind
    for i in range(len(line_list)):
        if in_element: #wenn wir in einem Element sind, werden alle folgenden Zeilen zu diesem Eintrag hinzugefügt
            if not re.search(pattern,line_list[i]):
                song_dict[element].extend([line_list[i]])
        match = re.search(pattern,line_list[i]) #Bis wir den ersten Match haben (zB VersX oder Chorus), gibt es auch kein Element
        if match: #Wenn wir jedoch ein Match haben, sind wir in einem Element. Dieses wird neu im Dictonary angelegt.
            in_element = True
            element = match.group(1)
            song_dict[element] = [] #Wir geben an, dass hinter diesem Dictonary Eintrag eine neue Liste steht.


    def createPDF(fontSize = 13):
        width, height = A4 #keep for later
        font = 'Helvetica'
        lineHeight = fontSize + .75 * fontSize
        wordSpace = 3
        boarder = inch
        topBoarder = .75*boarder
        instrSpaces = 5
        chordstyle = styles.ParagraphStyle('chord')
        chordstyle.fontSize = fontSize
        hstyle = styles.ParagraphStyle('heading')
        hstyle.fontSize = fontSize +1
        tstyle = styles.ParagraphStyle('title')
        tstyle.fontSize = fontSize +5
        copyrightstyle = styles.ParagraphStyle('copyright')
        copyrightstyle.fontSize = 8


        pattern = '\[([\w\d#/]+)\]'
        y = height - topBoarder - fontSize
        x = boarder
        realWidth = width - 2*boarder
        c = canvas.Canvas(path+info_dict['title']+'-'+info_dict['key']+'.pdf', pagesize=A4)
        c.setFont(font, fontSize-1)

        P1 = Paragraph("<u><b>"+info_dict['title']+"</b></u>",tstyle)
        P1.wrap(realWidth, height)
        P1.drawOn(c,x,y)

        if info_dict.has_key('key'):
            P1 = Paragraph("<b>"+info_dict['key']+"</b>",chordstyle)
            P1.wrap(realWidth, height)
            P1.drawOn(c,width-boarder-stringWidth(info_dict['key'], font, chordstyle.fontSize),y)
        if info_dict.has_key('bpm'):
            c.drawRightString(width-boarder,y-lineHeight,'%s'%info_dict['bpm'])
        P1 = Paragraph(info_dict['composer'],copyrightstyle)
        P1.wrap(realWidth, height)
        P1.drawOn(c,x,y-lineHeight)

        c.setFont(font, fontSize)
        y -= hstyle.fontSize + 2*lineHeight

        for key in song_dict:
            P1 = Paragraph("<b><i>"+key+"</i></b>",hstyle)
            P1.wrap(realWidth, height)
            P1.drawOn(c,x,y)
            xOfLast = boarder
            lineCount = 0
            if re.search(pattern, song_dict.get(key)[0]):
                y -= 1.8 * (lineHeight) #Abstand von Überschrift zu erster Zeile wenn Akkorde
            else:
                y -= 1.2 * (lineHeight) #Abstand von Überschrift zu erster Zeile wenn keine Akkorde
            if (key in ["Instrumental", "Intro"]):
                for line in song_dict.get(key):
                    line = line.replace('[','').replace(']','').replace(' ','&nbsp;'*(instrSpaces))
                    P1 = Paragraph("<b>"+line+"</b>",chordstyle)
                    P1.wrap(realWidth, height)
                    P1.drawOn(c,x,y)
                    y -= 1.5 * lineHeight #Abstand nach jedem Abschnitt
            else:
                for line in song_dict.get(key):
                    if ((xOfLast + stringWidth(line, font, fontSize)) < (width - boarder)) and (lineCount < 2):
                        x = xOfLast
                        lineCount += 1
                    elif not re.search(pattern, line):
                        y -= 1 * lineHeight
                    else:
                        y -= 1.5 * lineHeight
                        lineCount = 1
                    line = line.decode('utf-8')
                    last_was_chord = False
                    x_min = 0
                    cursor = 0
                    while cursor < len(line):
                        l = line[cursor]
                        if l == ' ':
                            if last_was_chord:
                                x += last_cord_length
                                last_was_chord = False
                            else:
                                x += wordSpace
                        elif l == '[':
                            end = line.find(']', cursor)
                            chord = line[cursor+1:end]
                            P1 = Paragraph("<b>"+chord+"</b>",chordstyle)
                            P1.wrap(realWidth, height)
                            if x < x_min:
                                x = x_min
                            P1.drawOn(c,x,y+fontSize+0.01*fontSize**2)
                            cursor = end
                            last_was_chord = True
                            last_cord_length = stringWidth(chord, font, fontSize)
                            x_min = x + last_cord_length + wordSpace*7
                        else:
                            last_was_chord = False
                            c.drawString(x,y,l)
                            x += stringWidth(l, font, fontSize)
                        cursor += 1
                    xOfLast = x + wordSpace
                    x = boarder
                y -= 1.5 * lineHeight #Abstand nach jedem Abschnitt


        P1 = Paragraph(u'\u00a9 '+
                       info_dict['copyright']+
                       '<br/>Gebrauch nur zur Nutzung im Rahmen von Veranstaltungen der City Chapel Stuttgart',copyrightstyle)
        P1.wrap(realWidth, height)
        P1.drawOn(c,x,boarder-P1.height)# + lineHeight)

        c.showPage()
        c.save()
        return(y < boarder)

    nochmal = True
    fontSize = 13
    while (nochmal):
        nochmal = createPDF(fontSize)
        fontSize -= .5
