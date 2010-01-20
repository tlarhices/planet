#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import urllib
import re

import general

class i18n:
  default = u"french"
  traductions = None
  langue = None
  
  def __init__(self, langue):
    """Prépare la traduction meugique !"""
    self.langue = langue
    self.traductions = {}
    
  def listeLangues(self):
    langues = ["french",]
    for langue in os.listdir(os.path.join(".", "data", "langues")):
      if langue.endswith(".i18n"):
        langues.append(langue[:-5])
    return langues
    
  def utf8ise(self, texte):
    if not isinstance(texte, unicode):
      texte = texte.decode("utf-8")
    return texte
    
  def getText(self, texte):
    """Retourne le texte traduit dans la langue souhaitée"""
    if texte == None:
      return u""
    
    if isinstance(texte, (float, int)):
      return texte
      
    if isinstance(texte, (unicode, str)):
      
      #Regarde si c'est un id de sprite
      if texte.lower().startswith("{s:"):
        return self.utf8ise(texte)

      out = ""
      for element in texte.split("\n"):
        out+=self.__getText__(texte=element.strip())+"\r\n"
      return out.strip()
      
    if isinstance(texte, dict):
      clef=texte.keys()
      contenu=self.getText(texte.values())
      texte = dict(zip(clef,contenu))
      return texte
      
    if isinstance(texte, list):
      out=[]
      for element in texte:
        out.append(self.getText(element))
      return out
      
    general.TODO("Ajouter i18n pour type "+str(type(texte)))
    print texte, "non géré par i18n"
    return texte
      
  def changeLangue(self, langue):
    self.langue=langue
    self.traductions = {}
    
  def __getText__(self, texte):
    """
    Cherche une ligne de texte dans la langue souhaitée
    À ne pas utiliser directement, utilisez getText qui va faire le boulot
    """
    self.langue = self.utf8ise(self.langue)
    self.default = self.utf8ise(self.default)
    texte = self.utf8ise(texte)
    
    #Si on est dans la langue d'origine du script, on saute
    if self.langue.lower().strip() == self.default.lower().strip():
      return texte
      
    #On regarde si on l'a dans le dico de traduction
    if texte.strip().lower() in self.traductions.keys():
      return self.utf8ise(self.traductions[texte.strip().lower()])
      
    #On regarde si on l'a dans le fichier
    depuisFichier = self.depuisFichier(texte=texte)
    if depuisFichier != None:
      return self.utf8ise(depuisFichier)
      
    #On l'a pas, on affiche un avertissement et on temporise dans le fichier de la langue
    #print "Avertissement :: i18n :: Pas de traduction pour \""+texte+"\"."+self.langue
    if not general.configuration.getConfiguration("affichage", "langue", "traductionAuto","f", bool):
      self.ajouterAuFichier(texte=texte, traduction=texte)
      return self.utf8ise(texte)
    else:
      texte_trad = self.translate(text=texte, fromLang="French", toLang=self.langue)
      self.ajouterAuFichier(texte=texte, traduction=texte_trad)
      return self.utf8ise(texte_trad)
    
  def ajouterAuFichier(self, texte, traduction):
    """Ajoute une nouvelle traduction au fichier de la langue courante"""
    fichierTrad = open(os.path.join(".", "data", "langues", self.langue+".i18n"), "a")
    texte = self.utf8ise(texte).strip().lower()
    texte = texte+"|^|"+self.utf8ise(traduction)+"\r\n"
    fichierTrad.write(texte.encode("utf-8"))
    fichierTrad.close()

  def depuisFichier(self, texte):
    """Recherche une traduction depuis le fichier de la langue courante et si elle existe la garde en ram"""
    try:
      fichierTrad = open(os.path.join(".", "data", "langues", self.langue+".i18n"))
    except IOError:
      #Cette langue n'existe pas
      print "Impossible de charger ce fichier de langue. Création d'un fichier vide"
      fichierTrad = open(os.path.join(".", "data", "langues", self.langue+".i18n"),"w")
      fichierTrad.close()
      return
      
    texte = texte.strip().lower()
      
    for ligne in fichierTrad:
      ligne = self.utf8ise(ligne.strip())
      texte = self.utf8ise(texte)
      if ligne != "":
        try:
          original, traduction = ligne.split("|^|")
          if original.strip().lower()==texte:
            self.traductions[original.strip().lower()]=traduction.strip()
            return self.utf8ise(traduction.strip())
        except ValueError:
          print u"Ligne mal formée dans le fichier de langue "+self.langue+u" : "+ligne
    fichierTrad.close()
    return None
    
#### De pas de moi mais de http://developer.spikesource.com/blogs/traya/2009/02/python_google_translator_pytra.html
#!/usr/bin/env python
# -*- coding: utf-8 -*-

  langCode={ "arabic":"ar", "bulgarian":"bg", "chinese":"zh-CN", "croatian":"hr", "czech":"cs", "danish":"da", "dutch":"nl", "english":"en", "finnish":"fi", "french":"fr", "german":"de", "greek":"el", "hindi":"hi", "italian":"it", "japanese":"ja", "korean":"ko", "norwegian":"no", "polish":"pl", "portugese":"pt", "romanian":"ro", "russian":"ru", "spanish":"es", "swedish":"sv" }

  def setUserAgent(self, userAgent):
    urllib.FancyURLopener.version = userAgent
    pass

  def translate(self, text, fromLang="English", toLang="German"):
    if fromLang.lower().strip() == toLang.lower().strip():
      return text
      
    self.setUserAgent("Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008070400 SUSE/3.0.1-0.1 Firefox/3.0.1")
    try:
        post_params = urllib.urlencode({"langpair":"%s|%s" %(self.langCode[fromLang.lower()],self.langCode[toLang.lower()]), "text":text.encode("utf-8"),"ie":"UTF8", "oe":"UTF8"})
    except KeyError, error:
        print "Currently we do not support %s" %(error.args[0])
        return
    page = urllib.urlopen("http://translate.google.com/translate_t", post_params)
    content = page.read()
    page.close()
    match = re.search("<span id=result_box class=\"short_text\">(.*?)</span>", content)
    value = match.groups()[0].split("onmouseout=\"this.style.backgroundColor='#fff'\">")[1].replace("% (f) .2 f%%", "%(f).2f%%").replace("% (a) .2 f%%", "%(a).2f%%")
    print value
    return u"AutoTrans : "+value
