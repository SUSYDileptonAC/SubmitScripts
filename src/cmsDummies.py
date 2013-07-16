class InputTag:
    def __init__(self,a,b,c):
        self.__content = (a,b,c)

    def __repr__(self):
        return "cms.InputTag(%s, %s, %s)"%(repr(self.__content[0]),
                                           repr(self.__content[1]),
                                           repr(self.__content[2]),)
