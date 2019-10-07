#*********************************************************************
# content   = main hub
# version   = 0.1.0
# date      = 2019-10-06
#
# license   = MIT <https://github.com/alexanderrichtertd>
# author    = Alexander Richter <alexanderrichtertd.com>
#*********************************************************************

import os
import sys

from extern import yaml

import pipefunc


#*********************************************************************
# VARIABLES
DATA_FORMAT = '.yml'
IMG_FORMAT  = '.png'


#*********************************************************************
class Singleton(object):
    def __new__(cls, *args, **kwds):

        self = "__self__"
        if not hasattr(cls, self):
            instance = object.__new__(cls)
            instance.init(*args, **kwds)
            setattr(cls, self, instance)
        return getattr(cls, self)

    def init(self, *args, **kwds):
        pass


#*********************************************************************
class Tank(Singleton):

    def init_os(self):
        self.user.setup()

    def init_software(self):
        self.software.setup()
        self.software.print_header()
        self.user.setup()

    @property
    def software(self):
        from software import Software
        return Software()

    @property
    def user(self):
        from users import User
        return User()

    @property
    def context(self):
        return self.software.context

    @property
    def log(self):
        import pipelog
        return pipelog


    #*********************************************************************
    # DATA
    @property
    def data(self):
        return self.get_data()

    @property
    def data_project(self):
        return self.get_data('project')

    @property
    def data_software(self):
        return self.get_data('software')

    @property
    def data_script(self):
        return self.get_data('script')

    @property
    def data_templates(self):
        return self.get_data('templates')

    @property
    def data_notice(self):
        return self.get_data('notice')

    @property
    def data_achievement(self):
        return self.get_data('achievement')


    #*********************************************************************
    # GET AND SET DATA
    def get_data(self, file_name='', user_id=os.getenv('username')):

        def get_all_data():
            config_data = {}
            data_user_files    = pipefunc.get_file_list(path=self.get_env('DATA_USER_PATH'),    file_type='*' + DATA_FORMAT)
            data_project_files = pipefunc.get_file_list(path=self.get_env('DATA_PROJECT_PATH'), file_type='*' + DATA_FORMAT)

            data_project_files = list(set(data_user_files)|set(data_project_files))
            for each_file in data_project_files: config_data.update({each_file : self.get_data(each_file, user_id)})
            return config_data

        if not file_name: return get_all_data()

        file_name = file_name.split('.')[0]
        file_path = ''

        if user_id and self.get_env('DATA_USER_OVERWRITE') == 'True':
            file_path = os.path.normpath(('/').join([self.get_env('DATA_USER_PATH'), file_name + DATA_FORMAT]))

        if not os.path.exists(file_path):
            file_path = os.path.normpath(('/').join([self.get_env('DATA_PROJECT_PATH'), file_name + DATA_FORMAT]))

        # OPEN data path
        if os.path.exists(file_path):
            return self.get_yml_file(file_path)

        else: self.log('CANT find file: {}'.format(file_path))
        return ''


    def set_data(self, path, key, value):
        if os.path.exists(path):
            tmp_content = self.get_yml_file(path)
        else:
            tmp_content = {}
            pipefunc.create_folder(path)
        tmp_content[key] = value
        self.set_yml_file(path, tmp_content)


    #*********************************************************************
    # PATH
    def get_pipeline_path(self, end_path):
        pipeline_path = os.getenv('PIPELINE_PATH')
        if not pipeline_path: return

        pipeline_path = pipeline_path.split(';')
        # find first fitting path
        for eachPath in pipeline_path:
            path = os.path.normpath(('/').join([eachPath,end_path]))

            if os.path.exists(path):
                return path

        return ''

    def get_img_path(self, end_path='btn/default'):
        if '.' in end_path: img_format = ''
        else: img_format = IMG_FORMAT

        path = self.get_pipeline_path('img/{}{}'.format(end_path, img_format))
        if not path: path = self.get_pipeline_path('img/{}/default{}'.format(os.path.dirname(end_path), IMG_FORMAT))
        if not path: path = self.get_pipeline_path('img/btn/default{}'.format(IMG_FORMAT))
        return path


    #*********************************************************************
    # YAML
    def set_yml_file(self, path, content):
        with open(path, 'w') as outfile:
            try:
                yaml.dump(content, outfile, default_flow_style=False)
            except yaml.YAMLError as exc:
                self.log(exc)


    def get_yml_file(self, path):
        try:
            with open(path, 'r') as stream:
                # STRING into DICT
                yml_content = yaml.load(stream)
                if yml_content: return yml_content
                else:
                    self.log('CANT load file: {}'.format(path))
        except yaml.YAMLError as exc:
            self.log(exc)

    # define & register custom tag handler
    # combine var with strings
    def join(loader, node):
        seq = loader.construct_sequence(node)
        return ''.join([str(i) for i in seq])

    # replace (multiple) ENV var
    def env(loader, node):
        seq  = loader.construct_sequence(node)
        path = os.getenv(seq[0])
        seq.pop(0)

        if not path: return ''
        path = path.split(';')

        new_env = ''
        for env in path:
            if new_env: new_env += ';'
            new_env += env
            if seq: new_env += ''.join([str(os.path.normpath(i)) for i in seq])
        return new_env

    # replace (multiple) with first ENV var
    def env_first(loader, node):
        seq  = loader.construct_sequence(node)
        path = os.getenv(seq[0])

        if ';' in path: path = path.split(';')[0]
        seq.pop(0)

        if seq: path += ''.join([str(os.path.normpath(i)) for i in seq])
        return path

    yaml.add_constructor('!env', env)
    yaml.add_constructor('!env_first', env_first)
    yaml.add_constructor('!join', join)


    #*********************************************************************
    # ENV
    #
    # @BRIEF  creates or add enviroment variable
    #
    # @PARAM  STRING var, STRING content
    def add_env(self, var, content):
        if not content: return

        # CHECK for list
        if isinstance(content, list):
            for item in content:
                self.add_env(var, item)
        else:
            content = str(content)

            # CHECK empty
            if os.environ.__contains__(var):
                os.environ[var] += ('').join([';', content])
            else:
                os.environ[var] = ('').join([content])
            return os.environ[var]

    # GET env or empty str & WARNING
    def get_env(self, var):
        if os.environ.__contains__(var):
            return os.environ[var].split(';')[0]
        self.log('ENV doesnt exist: {}'.format(var))
        return ''
