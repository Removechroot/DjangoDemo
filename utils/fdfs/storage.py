from django.core.files.storage import Storage
from fdfs_client.client import Fdfs_client
from django.conf import settings

class FDFSStorage(Storage):
    # fdfs文件存储
    def __init__(self,  client_conf=None, base_url=None):
        if client_conf  is None:
            client_conf = settings.FDFS_CLIENT_CONF
        self.client_conf = client_conf

        if base_url is None:
            base_url = settings.FDFS_URL
        self.base_url = base_url

    def _open(self, name, mode='rb'):
        pass

    def _save(self, name, content):
        # name:你选择的上传文件名字
        # content：包含你上传文件内容的file对象

        # 创建一个Fdfs_clier对象
        client = Fdfs_client(self.client_conf)

        # 上传文件到fastdfs中
        res = client.upload_by_buffer(content.read())
        # dict
        # {
        #     'Group name': group_name,
        #     'Remote file_id': remote_file_id,
        #     'Status': 'Upload successed.',
        #     'Local file name': local_file_name,
        #     'Uploaded size': upload_size,
        #     'Storage IP': storage_ip
        # }
        # if res.get('Status') != 'Upload successed':
        #     raise Exception('上传文件到fast dfs 失败')
        if res.get('Status') != 'Upload successed.':
            raise Exception('上传失败')

        filename = res.get('Remote file_id')
        print(filename)
        return filename

    def exists(self, name):
        '''判断文件名是否可用'''
        return False

    def url(self, name):
        return self.base_url+name
