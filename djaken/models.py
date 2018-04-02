from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from docutils.core import publish_parts
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


    def get_html_from_reST(self, reST_text):
 
        reST_content = reST_text

        html = publish_parts(reST_content, writer_name='html')['html_body']
        return html


    def save(self, saveRelevancyOnly=False, force_insert=False, force_update=False):

        if not saveRelevancyOnly:
            if self.is_encrypted:
                encryption_key = self.encryption_key
                self.encryption_key = ""
                self.encryption_iv, self.content_encrypted = self.encrypt(self.content, encryption_key)
                self.content = "*This note is encrypted.*"

            self.content_html = self.get_html_from_reST(self.content)

        super(Note, self).save(force_insert, force_update)


    def get_unencrypted_content(self, encryption_key):
        unencrypted_content = self.decrypt(self.content_encrypted, encryption_key)
        if unencrypted_content:
            unencrypted_content_html = self.get_html_from_reST(unencrypted_content)
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

