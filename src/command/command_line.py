import cmd


class CommandLine(cmd.Cmd):
    intro = 'Intro'
    prompt = '(router) '
    file = None

    def do_test(self, arg):
        'Test documentation'
        print("Test successful")

    def do_test_two(self, arg):
        'Test two documentation'
        print("Test two successful")


if __name__ == '__main__':
    CommandLine().cmdloop()
