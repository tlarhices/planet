#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import urllib
import re


class i18n:
  default = u"français"
  traductions = None
  langue = None
  interface = None
  
  def __init__(self, interface, langue):
    """Prépare la traduction meugique !"""
    self.langue = langue
    self.traductions = {}
    self.interface = interface
    
  def utf8ise(self, texte):
    if not isinstance(texte, unicode):
      texte = texte.decode("utf-8")
    return texte
    
  def getText(self, texte):
    """Retourne le texte traduit dans la langue souhaitée"""
    out = ""
    for element in texte.split("\n"):
      out+=self.__getText__(texte=element.strip())+"\r\n"
    return out.strip()
    
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
    
    #Si on est dans la langue d'origine du scripte, on saute
    if self.langue == self.default:
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
    if self.interface.configuration.getConfig(clef="traductionAuto", defaut="1")=="0":
      self.ajouterAuFichier(texte=texte, traduction=texte)
      return self.utf8ise(texte)
    else:
      texte_trad = self.translate(text=texte, fromLang="French", toLang=self.langue)
      self.ajouterAuFichier(texte=texte, traduction=texte_trad)
      return self.utf8ise(texte_trad)
    
  def ajouterAuFichier(self, texte, traduction):
    """Ajoute une nouvelle traduction au fichier de la langue courante"""
    if self.interface==None:
      return texte
      
    if self.interface.monde!=None:
      fichierTrad = self.interface.monde.getFichierDefault(nomFichier=self.langue+".i18n", mode="a")
    else:
      import os
      fichierTrad = open(os.path.join(".", "UI", "default", self.langue+".i18n"), "a")
    texte = self.utf8ise(texte).strip().lower()
    texte = texte+"|^|"+self.utf8ise(traduction)+"\r\n"
    fichierTrad.write(texte.encode("utf-8"))
    fichierTrad.close()

  def depuisFichier(self, texte):
    """Recherche une traduction depuis le fichier de la langue courante et si elle existe la garde en ram"""
    if self.interface==None:
      return texte
      
    try:
      if self.interface.monde!=None:
        fichierTrad = self.interface.monde.getFichierDefault(nomFichier=self.langue+".i18n", mode="r")
      else:
        import os
        fichierTrad = open(os.path.join(".", "UI", "default", self.langue+".i18n"))
    except IOError:
      #Cette langue n'existe pas
      self.interface.afficheAvertissement("Impossible de charger ce fichier de langue.")
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
          self.interface.afficheAvertissement("Ligne mal formée dans le fichier de langue "+self.langue+" : "+ligne)
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
    self.setUserAgent("Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008070400 SUSE/3.0.1-0.1 Firefox/3.0.1")
    try:
        post_params = urllib.urlencode({"langpair":"%s|%s" %(self.langCode[fromLang.lower()],self.langCode[toLang.lower()]), "text":text.encode("utf-8"),"ie":"UTF8", "oe":"UTF8"})
    except KeyError, error:
        self.interface.afficheErreur("Currently we do not support %s" %(error.args[0]))
        return
    page = urllib.urlopen("http://translate.google.com/translate_t", post_params)
    content = page.read()
    page.close()
    match = re.search("<div id=result_box dir=\"ltr\">(.*?)</div>", content)
    value = match.groups()[0]
    return value
