from __future__ import unicode_literals

import re
import binascii
import base64

try:
    from Crypto.Cipher import AES
    can_decrypt_frag = True
except ImportError:
    can_decrypt_frag = False

from youtube_dl.downloader.fragment import FragmentFD
from youtube_dl.downloader.external import FFmpegFD

from youtube_dl.compat import (
    compat_urllib_error,
    compat_urlparse,
    compat_struct_pack,
)
from youtube_dl.utils import (
    parse_m3u8_attributes,
    update_url_query,
)


class HotmartFD(FragmentFD):
    """ A limited implementation that does not require ffmpeg """

    FD_NAME = 'hlsnative_hotmart'

    @staticmethod
    def can_download(manifest, info_dict=dict()):
        return True

    def real_download(self, filename, info_dict):
        man_url = info_dict['url']
        self.to_screen('[%s] Downloading m3u8 manifest' % self.FD_NAME)

        urlh = self.ydl.urlopen(self._prepare_url(info_dict, man_url))
        man_url = urlh.geturl()
        s = urlh.read().decode('utf-8', 'ignore')

        if not self.can_download(s, info_dict):
            if info_dict.get('extra_param_to_segment_url') or info_dict.get('_decryption_key_url'):
                self.report_error('pycrypto not found. Please install it.')
                return False
            self.report_warning(
                'hlsnative has detected features it does not support, '
                'extraction will be delegated to ffmpeg')
            fd = FFmpegFD(self.ydl, self.params)
            for ph in self._progress_hooks:
                fd.add_progress_hook(ph)
            return fd.real_download(filename, info_dict)

        def is_ad_fragment_start(s):
            return (s.startswith('#ANVATO-SEGMENT-INFO') and 'type=ad' in s
                    or s.startswith('#UPLYNK-SEGMENT') and s.endswith(',ad'))

        def is_ad_fragment_end(s):
            return (s.startswith('#ANVATO-SEGMENT-INFO') and 'type=master' in s
                    or s.startswith('#UPLYNK-SEGMENT') and s.endswith(',segment'))

        media_frags = 0
        ad_frags = 0
        ad_frag_next = False
        for line in s.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith('#'):
                if is_ad_fragment_start(line):
                    ad_frag_next = True
                elif is_ad_fragment_end(line):
                    ad_frag_next = False
                continue
            if ad_frag_next:
                ad_frags += 1
                continue
            media_frags += 1

        ctx = {
            'filename': filename,
            'total_frags': media_frags,
            'ad_frags': ad_frags,
        }

        self._prepare_and_start_frag_download(ctx)

        fragment_retries = self.params.get('fragment_retries', 5)
        skip_unavailable_fragments = self.params.get('skip_unavailable_fragments', True)
        test = self.params.get('test', False)

        extra_query = None
        extra_param_to_segment_url = info_dict.get('extra_param_to_segment_url')
        if extra_param_to_segment_url:
            extra_query = compat_urlparse.parse_qs(extra_param_to_segment_url)
        i = 0
        media_sequence = 0
        decrypt_info = {'METHOD': 'NONE'}
        byte_range = {}
        frag_index = 0
        ad_frag_next = False
        for line in s.splitlines():
            line = line.strip()
            if line:
                if not line.startswith('#'):
                    if ad_frag_next:
                        continue
                    frag_index += 1
                    if frag_index <= ctx['fragment_index']:
                        continue
                    frag_url = (
                        line
                        if re.match(r'^https?://', line)
                        else compat_urlparse.urljoin(man_url, line))
                    if extra_query:
                        frag_url = update_url_query(frag_url, extra_query)
                    count = 0
                    headers = info_dict.get('http_headers', {})
                    if byte_range:
                        headers['Range'] = 'bytes=%d-%d' % (byte_range['start'], byte_range['end'])
                    while count <= fragment_retries:
                        try:
                            success, frag_content = self._download_fragment(
                                ctx, frag_url, info_dict, headers)
                            if not success:
                                return False
                            break
                        except compat_urllib_error.HTTPError as err:
                            # Unavailable (possibly temporary) fragments may be served.
                            # First we try to retry then either skip or abort.
                            # See https://github.com/ytdl-org/youtube-dl/issues/10165,
                            # https://github.com/ytdl-org/youtube-dl/issues/10448).
                            self.to_screen('[%s] Error - %s - %s' % (self.FD_NAME, err.reason, headers))
                            count += 1
                            if count <= fragment_retries:
                                self.report_retry_fragment(err, frag_index, count, fragment_retries)
                    if count > fragment_retries:
                        if skip_unavailable_fragments:
                            i += 1
                            media_sequence += 1
                            self.report_skip_fragment(frag_index)
                            continue
                        self.report_error(
                            'giving up after %s fragment retries' % fragment_retries)
                        return False
                    if decrypt_info['METHOD'] == 'AES-128':
                        iv = decrypt_info.get('IV') or compat_struct_pack('>8xq', media_sequence)
                        decrypt_info['KEY'] = decrypt_info.get('KEY') or self.ydl.urlopen(
                            self._prepare_url(info_dict, info_dict.get('_decryption_key_url') or decrypt_info['URI'])).read()
                        frag_content = AES.new(
                            decrypt_info['KEY'], AES.MODE_CBC, iv).decrypt(frag_content)
                    self._append_fragment(ctx, frag_content)
                    # We only download the first fragment during the test
                    if test:
                        break
                    i += 1
                    media_sequence += 1
                elif line.startswith('#EXT-X-KEY'):
                    decrypt_url = decrypt_info.get('URI')
                    decrypt_info = parse_m3u8_attributes(line[11:])
                    if decrypt_info['METHOD'] == 'AES-128':
                        if 'IV' in decrypt_info:
                            decrypt_info['IV'] = binascii.unhexlify(decrypt_info['IV'][2:].zfill(32))
                        if decrypt_info['URI'].startswith('chave://'):
                            encrypted_url = decrypt_info['URI'].replace('chave://', '')
                            encrypted_url = binascii.a2b_base64(encrypted_url)

                            key = '49bded6736cb71dee90a0ddc3552f7483b20a20630b8d05541628d89f2691fb4'
                            iv  = '49bded6736cb71dee90a0ddc3552f748'

                            key = binascii.a2b_hex(key)
                            iv  = binascii.a2b_hex(iv)

                            aes = AES.new(key, AES.MODE_CBC, iv)
                            decrypted_url = aes.decrypt(encrypted_url)
                            
                            decrypt_info['URI'] = decrypted_url.decode().strip()
                        elif not re.match(r'^https?://', decrypt_info['URI']):
                            self.to_screen('[%s] Strange key - %s' % (self.FD_NAME, decrypt_info['URI']))
                            decrypt_info['URI'] = compat_urlparse.urljoin(
                                man_url, decrypt_info['URI'])

                            self.to_screen('[%s] Strange key - %s' % (self.FD_NAME, decrypt_info['URI']))
                        if extra_query:
                            decrypt_info['URI'] = update_url_query(decrypt_info['URI'], extra_query)
                        if decrypt_url is not None and decrypt_url != decrypt_info['URI']:
                            self.to_screen('[%s] Strange key - %s - %s' % (self.FD_NAME, decrypt_url, decrypt_info['URI']))
                            decrypt_info['KEY'] = None
                elif line.startswith('#EXT-X-MEDIA-SEQUENCE'):
                    media_sequence = int(line[22:])
                elif line.startswith('#EXT-X-BYTERANGE'):
                    splitted_byte_range = line[17:].split('@')
                    sub_range_start = int(splitted_byte_range[1]) if len(splitted_byte_range) == 2 else byte_range['end']
                    byte_range = {
                        'start': sub_range_start,
                        'end': sub_range_start + int(splitted_byte_range[0]),
                    }
                elif is_ad_fragment_start(line):
                    ad_frag_next = True
                elif is_ad_fragment_end(line):
                    ad_frag_next = False

        self._finish_frag_download(ctx)

        return True

