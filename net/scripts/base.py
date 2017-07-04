class BaseScript(object):
    name = 'Base script'
    description = "Full Description of script"
    params = dict({
        'target': 'required'
    })

    def config(self):
        return {
            'name': self.name,
            'description': self.description,
            'params': self.params
        }


"""
View -> DB. it get info still from DB.

DB -> script name, params

starter -> gets script_id, destinations, and calls celery task


script_config

tasks (registered!) -> uses class task for work

class for work

"""
