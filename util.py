from apiclient import discovery
from httplib2 import Http
from oauth2client import client, file, tools

from dataclasses import dataclass

# things must be convertible to JSON format, almost everything should inherit this
# define json format to be a composition of list, map, strings and numbers
# i.e. don't actually turn to JSON string
class JsonConvertible:
    def convertToJson(self):
        raise NotImplementedError()

# represent an image. not to be confused with other Image class that's often used
class ImageTag(JsonConvertible):
    def __init__(self, contentUri: str, altText: str, sourceUri: str):
        self.contentUri = contentUri
        self.altText = altText
        self.sourceUri = sourceUri

    def convertToJson(self):
        return {
            "contentUri": self.contentUri,
            "altText": self.altText,
            "sourceUri": self.sourceUri
        }

# defines an item, generic
class Item(JsonConvertible):
    def __init__(self, title: str, description: str):
        self.title = title
        self.description = description

    def convertToJson(self):
        return {"title": self.title, "description": self.description}

class SingleChoiceItem(Item):
    def __init__(self, title: str, description: str, 
                 shuffle: bool = False, required: bool = True, img: ImageTag = None):
        super().__init__(title, description)
        self.shuffle = shuffle
        self.required = required
        self.img = img
        self.choice_ls = []

    # if goToSectionId is None, then it is submit form
    def addChoice(self, value: str, goToSectionId: str = None, img: ImageTag = None):
        new_choice = {
            "value": value
        }
        if goToSectionId is not None:
            new_choice["goToSectionId"] = goToSectionId
        else:
            new_choice["goToAction"] = "SUBMIT_FORM"
        if self.img is not None:
            new_choice["image"] = img.convertToJson()
        self.choice_ls.append(new_choice)
            
    def convertToJson(self):
        result = super().convertToJson()
        result.update({
            "questionItem": {
                "question": {
                    "required": self.required,
                    "choiceQuestion": {
                        "type": "RADIO",
                        "options": self.choice_ls,
                        "shuffle": self.shuffle
                    }
                },
            }
        })
        if self.img is not None:
            result["questionItem"]["image"]: self.img.convertToJson()
        return result

class TextItem(Item):
    def __init__(self, title: str, description: str):
        super().__init__(title, description)

    def convertToJson(self):
        result = super().convertToJson()
        result.update({
            "textItem": {}
        })
        return result

class PageBreakItem(Item):
    def __init__(self, id: str, title: str, description: str):
        super().__init__(title, description)
        self.id = id

    def convertToJson(self):
        result = super().convertToJson()
        result.update({
            "itemId": self.id,
            "pageBreakItem": {}
        })
        return result

# a section is a page rendered, which is a list of items
class Section(JsonConvertible):
    def __init__(self, id: str, title: str, description: str):
        self.item_ls = [PageBreakItem(id, title, description)]
    def addItems(self, *items: Item):
        self.item_ls.extend(items)
    def convertToJson(self):
        return [item.convertToJson() for item in self.item_ls]

# Form contains (multiple) sections
# it should deal with all section concatenation problems (e.g. page break)
class Form(JsonConvertible):
    def __init__(self, title: str):
        self.title = title
        self.section_ls = []
    def addSections(self, *sections: Section):
        self.section_ls.extend(sections)
    def convertToJson(self):
        return {
            "info": {
                "title": self.title,
            }
        }
    
# a world state is a representation of world scenario
# (e.g. is the button pressed? does the player have some item?)
# a world state should be a data class, and should have the ability
# to encode itself to unique integer in range [0, lenAllStates()].
# lenAllStates() should return the number of all possible states
# It should also provide an generator that iterates through all
# possible world states.
class WorldState:
    def encodeState(self) -> int:
        raise NotImplementedError()
    @classmethod
    def iterAllStates(cls):
        raise NotImplementedError()
    @classmethod
    def lenAllStates(cls) -> int:
        raise NotImplementedError()

# A scene is a section factory, generate section based by world state
# the section it generates should have the same id it makes
class Scene:
    base = 0
    @classmethod
    def generateSection(cls, ws: WorldState) -> Section:
        raise NotImplementedError()
    @classmethod
    def getId(cls, ws: WorldState) -> str:
        return str(cls.base + ws.encodeState())

# A singlescene is a scene that would only need to be made once
# i.e. don't need to embed world state
# You can make the entrance or exit scene by this
class SingleScene:
    base = 0
    @classmethod
    def generateSection(cls) -> Section:
        raise NotImplementedError()
    @classmethod
    def getId(cls) -> str:
        return str(cls.base)
        

# ---

# from Google Form API example
def getFormService():
    SCOPES = "https://www.googleapis.com/auth/forms.body"
    DISCOVERY_DOC = "https://forms.googleapis.com/$discovery/rest?version=v1"
    store = file.Storage('token.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('client_secrets.json', SCOPES)
        creds = tools.run_flow(flow, store)

    form_service = discovery.build('forms', 'v1', http=creds.authorize(
        Http()), discoveryServiceUrl=DISCOVERY_DOC, static_discovery=False)
    return form_service

# makes form specified by Form
# is dependent on PageBreakItem...
def createForm(form: Form, start_goto_id: str):
    # make form
    form_service = getFormService()
    result = form_service.forms().create(body=form.convertToJson()).execute()
    form_id = result["formId"]
    print(f'form_id: {form_id}')

    # add most items to form, note the sequence
    items = [item for section in form.section_ls for item in section.item_ls]
    pb_items = [item for item in items if issubclass(type(item), PageBreakItem)]
    request = {
        "requests": [{
                "createItem": {
                    "item": item.convertToJson(),
                    "location": {"index": i}
                }
            } 
            for i, item in enumerate(pb_items)
        ]
    }
    question_setting = form_service.forms().batchUpdate(formId=form_id, body=request).execute()

    request = {
        "requests": [
            {
                "createItem": {
                    "item": item.convertToJson(),
                    "location": {"index": i}
                }
            } 
            for i, item in enumerate(items) if not issubclass(type(item), PageBreakItem)
        ]
    }
    question_setting = form_service.forms().batchUpdate(formId=form_id, body=request).execute()

    # add a starting question that redirects to the correct starting scene
    choice = SingleChoiceItem("Start", "")
    choice.addChoice("Go", start_goto_id)
    request = {
        "requests": [
            {
                "createItem": {
                    "item": choice.convertToJson(),
                    "location": {"index": 0}
                }
            } 
        ]
    }
    question_setting = form_service.forms().batchUpdate(formId=form_id, body=request).execute()
    return form_id

# assign ID (range) to classes
def assignId(scene_cls_ls: list[type], single_scene_cls_ls: list[type], worldstate_cls: type):
    for i, cls in enumerate(single_scene_cls_ls):
        cls.base = i
    for i, cls in enumerate(scene_cls_ls):
        cls.base = len(single_scene_cls_ls) + worldstate_cls.lenAllStates() * i
    