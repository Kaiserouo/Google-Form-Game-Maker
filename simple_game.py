from util import *

# let's make a simple door & button scene
# world states defines what kind of world states there are
# there are only 2 states: either the button is pressed or not
@dataclass
class MyWorldState(WorldState):
    isButtonPressed: bool = False
    def encodeState(self) -> int:
        return int(self.isButtonPressed)
    @classmethod
    def iterAllStates(cls):
        for iBP in [True, False]:
            yield MyWorldState(isButtonPressed = iBP)
    @classmethod
    def lenAllStates(cls) -> int:
        return 2

# defines scene
# door scene needs to open the door and change the options based on world state
class DoorScene(Scene):
    @classmethod
    def generateSection(cls, ws: MyWorldState) -> Section:
        door_m = {
            False: "There is a closed door.",
            True: "The door is open now."
        }

        sec = Section(cls.getId(ws), "Door", door_m[ws.isButtonPressed])

        choice = SingleChoiceItem("What to do now?", "")
        choice.addChoice("Look back", ButtonScene.getId(ws))
        if ws.isButtonPressed:
            choice.addChoice("Get out", EndingScene.getId())

        sec.addItems(choice)
        return sec

# button scene needs to have the "Press button" option when the button isn't pressed.
# changes the world state to "button pressed" when choosing "Press Button"
class ButtonScene(Scene):
    @classmethod
    def generateSection(cls, ws: MyWorldState) -> Section:
        button_m = {
            False: "There is a button.",
            True: "The button is pressed."
        }
        
        sec = Section(cls.getId(ws), "Button", button_m[ws.isButtonPressed])

        choice = SingleChoiceItem("What to do now?", "")
        choice.addChoice("Look back", DoorScene.getId(ws))
        if not ws.isButtonPressed:
            choice.addChoice("Press button", ButtonScene.getId(MyWorldState(isButtonPressed=True)))

        sec.addItems(choice)
        return sec

# serves as an ending after getting out of the door, just go back or end the form
# also ending does not need to duplicate, use SingleScene
class EndingScene(SingleScene):
    @classmethod
    def generateSection(cls) -> Section:
        sec = Section(cls.getId(), "Ending", "You escaped. Yay!")

        choice = SingleChoiceItem("Restart", "")
        choice.addChoice("Restart", DoorScene.getId(MyWorldState(isButtonPressed=False)))
        choice.addChoice("End game", None)  # note that if does not specify ID, then assume action "submit".

        sec.addItems(choice)
        return sec

# main program
if __name__ == '__main__':
    # (adjust here)
    # List[Scene]
    scene_cls_ls = [DoorScene, ButtonScene]
    # List[SingleScene]
    single_scene_cls_ls = [EndingScene]
    # your WorldState class
    world_state_cls = MyWorldState
    # the start position
    start_goto_id = DoorScene.getId(MyWorldState(isButtonPressed=False))

    # the rest is almost fixed, leave it as it is
    assignId(scene_cls_ls, single_scene_cls_ls, world_state_cls)
    
    form = Form("Simple Game")
    for ws in world_state_cls.iterAllStates():
        for scene in scene_cls_ls:
            form.addSections(scene.generateSection(ws))
    for scene in single_scene_cls_ls:
        form.addSections(scene.generateSection())
    
    createForm(form, start_goto_id)