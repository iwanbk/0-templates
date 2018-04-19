from zerorobot.template.base import TemplateBase


class Hello(TemplateBase):

    version = '0.0.1'
    template_name = "hello"

    def __init__(self, name=None, guid=None, data=None):
        super().__init__(name=name, guid=guid, data=data)

        if not self.data['msg']:
            self.data['msg'] = "Hello Robot"

    def echo_to_temp(self):
        j.sal.fs.writeFile("/tmp/msg.robot", self.data['msg'], append=True)
