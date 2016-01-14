from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
import markdown
from Crypto.Cipher import AES
from Crypto import Random
import base64
import hashlib

class Note(models.Model):

    author = models.ForeignKey('auth.User')
    title = models.CharField(max_length=255)
    content = models.TextField()
    content_html = models.TextField(editable=False)                    # don't want to see this in Admin
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    relevant = models.BooleanField(default=True)
    is_encrypted = models.BooleanField(default=False, editable=False)  # don't want to see this in Admin
    content_encrypted = models.TextField(editable=False)               # don't want to see this in Admin
    encryption_iv = models.CharField(max_length=64, editable=False)    # don't want to see this in Admin
    encryption_key = ""                                                # Only used momentarily to pass the key to the save function

    def autoAddLineBreaks(self, mdText):

        mdTextWithLineBreaks = ""
  
        for cIndex in range(len(mdText)):
            if ( 
                   ( cIndex == 1 and mdText[cIndex : cIndex + 2] == "\r\n" ) 
                   or 
                   ( 
                       cIndex > 1 and cIndex < (len(mdText) - 1) 
                       and  
                       mdText[cIndex : cIndex + 2] == "\r\n" 
                       and 
                       mdText[cIndex - 2 : cIndex] != "\r\n" 
                       and not 
                       ( 
                           cIndex < (len(mdText) - 3) 
                           and 
                           mdText[cIndex + 2 : cIndex + 4] == "\r\n" 
                       ) 
                       and not 
                       ( 
                           cIndex > 2 and mdText[cIndex - 2 : cIndex] == "  " 
                       ) 
                   ) 
               ):
                nextChars = "  " + mdText[cIndex]
            else:
                nextChars = mdText[cIndex]
 
            mdTextWithLineBreaks = mdTextWithLineBreaks + nextChars

        return mdTextWithLineBreaks


    def autoAddLinkTags(self, mdText):

        mdTextWithLinkTags = mdText
        urlVertices = []
        urlVerticesUntagged = []

        # First we find the vertices (start and end of the URL), inclusive off any existing end tags ('>' or ')').
        # A vertex is represented as a tuple (a,b) where 'a' is the index of "h" (in "http://...") and 'b' is the index of the last character in the URL.

        for cIndex in range(len(mdText)):
            if ( cIndex < (len(mdText) - 10) and ( mdText[cIndex : cIndex + 7] == "http://" or mdText[cIndex : cIndex + 8] == "https://") ):
                for cIndexURL in range(len(mdText) - cIndex - 7):
                    cIndexOffset = cIndexURL + cIndex + 7
                    if ( mdText[cIndexOffset : cIndexOffset + 1] == " " ) or ( mdText[cIndexOffset : cIndexOffset + 2] == "\r\n" ):
                        if mdText[cIndexOffset - 1] == ")" or mdText[cIndexOffset - 1] == ">":
                            urlVertices.append((cIndex, cIndexOffset - 2))
                        else:
                            urlVertices.append((cIndex, cIndexOffset - 1))
                        break
                    elif ( cIndexOffset == (len(mdText) - 1) ):
                        if mdText[cIndexOffset] == ")" or mdText[cIndexOffset] == ">":
                            urlVertices.append((cIndex, cIndexOffset - 1))
                        else:
                            urlVertices.append((cIndex, cIndexOffset))
                        break

        # Next we remove any vertices of already tagged URLs.

        for i in range(len(urlVertices)):
            vertex = urlVertices[i]
            linkIndexFirst = vertex[0]
            linkIndexLast = vertex[1]
            if not ( (linkIndexFirst > 0 and mdText[linkIndexFirst - 1] == "<" and linkIndexLast < (len(mdText) -1) and mdText[linkIndexLast + 1] == ">")
                     or 
                     (linkIndexFirst > 1 and mdText[linkIndexFirst - 2] == "]" and mdText[linkIndexFirst - 1] == "(" and linkIndexLast < (len(mdText) - 1) and mdText[linkIndexLast + 1] == ")") 
                   ):
                urlVerticesUntagged.append(vertex)

        # Then we insert tags around the untagged URL vertices.

        for i in range(len(urlVerticesUntagged)):
            vertex = urlVerticesUntagged[i]
            if i == 0:
                mdTextWithLinkTags = mdText[0:vertex[0]]
            else:
                previousVertex = urlVerticesUntagged[i-1]
                mdTextWithLinkTags = mdTextWithLinkTags + mdText[ previousVertex[1] + 1 : vertex[0] ]
            mdTextWithLinkTags = mdTextWithLinkTags + "<"
            mdTextWithLinkTags = mdTextWithLinkTags + mdText[ vertex[0] : vertex[1] + 1 ]
            mdTextWithLinkTags = mdTextWithLinkTags + ">"
            if i == len(urlVerticesUntagged) - 1:
                mdTextWithLinkTags = mdTextWithLinkTags + mdText[vertex[1] + 1 :]

        return mdTextWithLinkTags


    def get_html_from_markdown(self, markdown_text):
        
        markdown_content = markdown_text
        
        if getattr(settings, "DJAKEN_MARKDOWN_AUTO_ADD_LINK_TAGS", True):
            markdown_content = self.autoAddLinkTags(markdown_content)

 
        if getattr(settings, "DJAKEN_MARKDOWN_AUTO_ADD_LINE_BREAKS", True):
            markdown_content = self.autoAddLineBreaks(markdown_content)

        html = markdown.markdown(markdown_content)
        return html


    def save(self, force_insert=False, force_update=False):

        if self.is_encrypted:
            encryption_key = self.encryption_key
            self.encryption_key = ""
            self.encryption_iv, self.content_encrypted = self.encrypt(self.content, encryption_key)
            self.content = "*This note is encrypted.*"

        self.content_html = self.get_html_from_markdown(self.content)

        super(Note, self).save(force_insert, force_update)


    def get_unencrypted_content(self, encryption_key):
        unencrypted_content = self.decrypt(self.content_encrypted, encryption_key)
        if unencrypted_content:
            unencrypted_content_html = self.get_html_from_markdown(unencrypted_content)
            return True, unencrypted_content, unencrypted_content_html
        else:
            return False, "", ""


    def encrypt(self, raw_text, raw_key):
        key = hashlib.md5(raw_key.encode('utf-8')).digest()
        iv = Random.new().read(AES.block_size)
        iv_encoded = base64.b64encode(iv)
        cipher = AES.new( key, AES.MODE_CFB, iv) 
        encrypted_bytes = cipher.encrypt(raw_text.encode('utf-8'))
        encrypted_text_encoded = base64.b64encode(encrypted_bytes)

        return iv_encoded, encrypted_text_encoded


    def decrypt(self, encrypted_text_encoded, raw_key):
        try:
            key = hashlib.md5(raw_key.encode('utf-8')).digest()
            iv = base64.b64decode(self.encryption_iv)
            encrypted_bytes = base64.b64decode(encrypted_text_encoded)
            cipher = AES.new( key, AES.MODE_CFB, iv) 
            decrypted_text_encoded = cipher.decrypt(encrypted_bytes)
            decrypted_text = decrypted_text_encoded.decode('utf-8')
    
            return decrypted_text
        except:
            return False


    class Meta:
        ordering = ['-relevant', '-modified']
