import argparse, sys, os, time, getpass, ast, re, pyone

###################################################################################################

STATE = {"-2": "Any state, including DONE", "-1": "Any state, except DONE", "0": "INIT", "1": "PENDING", "2": "HOLD", "3": "ACTIVE", "4": "STOPPED", "5": "SUSPENDED", "6": "DONE", "8": "POWEROFF", "9": "UNDEPLOYED", "10": "CLONING", "11": "CLONING_FAILURE"}
token_file = os.path.join(os.path.expanduser('~'),'.pyone_token')

class Token(object):
    @staticmethod
    def token_get(token_file):
        if os.path.exists(token_file):
            token = []
            with open(token_file, 'r') as file:
                linefile = file.readline()
            for line in linefile.split("|"):
                token.append(line)
            return (True, token)
        else:
            return (False, "Token file not exists")

    @staticmethod
    def token_set(token_file, uri=None, user=None, timeout=None):
        if uri == None:
            status, old_token = Token.token_get(token_file)
            if status:
                uri = old_token[0]
            else:
                raise Exception("URI not found. You need launch 'token create' with '--uri' argument")
        if user == None:
            status, old_token = Token.token_get(token_file)
            if status:
                user = old_token[1]
            else:
                raise Exception("User not found. You need launch 'token create' with '--user' argument")
        if timeout == None:
            timeout = 3600

        # check uri
        if re.match(regex, uri) is None:
            raise Exception("URI is not well formed")

        print("URI: "+uri)
        print("User: "+user)
        form_password = getpass.getpass(prompt='Password: ')
        one_server = pyone.OneServer(uri, user+":"+form_password)
        token = one_server.user.login(user, "", timeout, -1)
        with open(token_file, 'w') as file:
            file.write(str(uri+"|"+user+"|"+token))
        return (True, "Token created")
    
    @staticmethod
    def token_del(token_file):
        if os.path.exists(token_file):
            os.remove(token_file)
            return (True, "Token deleted")
        else:
            return (False, "Token file not exists")

class one(object):
    one_server = None

    def __init__(self, token):
        self.one_server = pyone.OneServer(token[0], session=token[1]+":"+token[2])

    ## GET ALL VMs
    def get_vms(self):
        cmd_result = self.one_server.vmpool.info(-1,-1,-1,-1)
        return (True, cmd_result.VM)

    ## GET VM
    def get_vm(self, id):
        try:
            cmd_result = self.one_server.vm.info(id)
            return (True, cmd_result)
        except pyone.OneAuthorizationException as e:
            if 'Not authorized to perform USE VM' in e.args[0]:
                return (False, "Not authorized to make actions over VM "+str(id))
            else:
                raise

    ## GET ALL TEMPLATES
    def get_templates(self):
        cmd_result = self.one_server.templatepool.info(-1,-1,-1)
        return (True, cmd_result.VMTEMPLATE)

    ## GET TEMPLATE
    def get_template(self, id):
        cmd_result = self.one_server.template.info(id)
        return (True, cmd_result)

    ## VM START
    def vm_start(self, id):
        try:
            cmd_result = self.one_server.vm.action("resume",id)
            if cmd_result == id:
                return (True, "VM "+str(id)+" has been started")
            else:
                raise Exception(cmd_result)
        except pyone.OneActionException as e:
            if '[one.vm.action] Error performing action "resume": This action is not available for state RUNNING' in e.args[0]:
                return (False, "VM "+str(id)+" has already been started")
            elif '[one.vm.action] Error performing action "resume": This action is not available for state SHUTDOWN_UNDEPLOY' in e.args[0]:
                return (False, "VM "+str(id)+" it's stopping now, wait for more actions")
            elif '[one.vm.action] Error performing action "resume": This action is not available for state PENDING' in e.args[0]:
                return (False, "VM "+str(id)+" it's starting now, wait for more actions")
            elif '[one.vm.action] Error performing action "resume": This action is not available for state BOOT_UNDEPLOY' in e.args[0]:
                return (False, "VM "+str(id)+" it's starting now, wait for more actions")
            else:
                raise
    ## VM STOP
    def vm_stop(self, id):
        try:
            cmd_result = self.one_server.vm.action("undeploy",id)
            if cmd_result == id:
                return (True, "VM "+str(id)+" has been stopped")
            else:
                raise Exception(cmd_result)
        except pyone.OneActionException as e:
            if '[one.vm.action] Error performing action "undeploy": This action is not available for state UNDEPLOYED' in e.args[0]:
                return (False, "VM "+str(id)+" has already been stopped")
            elif '[one.vm.action] Error performing action "undeploy": This action is not available for state PENDING' in e.args[0]:
                return (False, "VM "+str(id)+" it's starting now, wait for more actions")
            elif '[one.vm.action] Error performing action "undeploy": This action is not available for state SHUTDOWN_UNDEPLOY' in e.args[0]:
                return (False, "VM "+str(id)+" it's stopping now, wait for more actions")
            else:
                raise
        except pyone.OneAuthorizationException as e:
            if 'Not authorized to perform MANAGE VM' in e.args[0]:
                return (False,"Not authorized to stop VM "+str(id))
            else:
                raise

    ## VM CREATE FROM ZERO
    def vm_create(self, specs):
        # first, check if vm name exists
        status, vms = self.get_vms()
        for vm in vms:
            if vm.NAME == specs['NAME']:
                raise Exception("ERROR: VM NAME EXISTS")

        # second, build xml query
        query_list = []
        for key,value in specs.items():
            if isinstance(value,list):
                for subelem in value:
                    subdict = ', '.join(['%s="%s"' % (subkey, subvalue) for subkey,subvalue in subelem.items()])
                    query_list.append('%s=[%s]' % (key, subdict))
            else:
                query_list.append('%s="%s"' % (key, value))
        query = ' '.join(query_list)

        return self.one_server.vm.allocate(query)

    ## VM CREATE FROM TEMPLATE
    def vm_create_template(self, template_id, specs, vm_name=""):
        # first, check if vm name exists
        status, vms = self.get_vms()
        for vm in vms:
            if vm.NAME == vm_name:
                raise Exception("ERROR: VM NAME EXISTS")

        # second, build xml query
        query_list = []
        for key,value in specs.items():
            if isinstance(value,list):
                for subelem in value:
                    subdict = ', '.join(['%s="%s"' % (subkey, subvalue) for subkey,subvalue in subelem.items()])
                    query_list.append('%s=[%s]' % (key, subdict))
            else:
                query_list.append('%s="%s"' % (key, value))
        query = ' '.join(query_list)

        return self.one_server.template.instantiate(template_id, vm_name, False, query, False)

    ## VM DESTROY
    def vm_destroy(self, id, force=False):
        if not force:
            print("Tidy shutdown")
            result,vm = self.get_vm(id)
            if result:
                if vm.STATE == 9:
                    cmd_result = self.one_server.vm.action("terminate-hard",id)
                    if cmd_result == id:
                        return (True, "The VM has been destroyed")
                    else:
                        return (False, cmd_result)
                elif vm.STATE == 6:
                    return (True, "The VM has already been destroyed")
                else:
                    # first, undeploy
                    self.one_server.vm.action("undeploy",id)
                    while(True):
                        # second, check if status is UNDEPLOYED
                        result,vm = self.get_vm(id)
                        if vm.STATE == 9:
                            cmd_result = self.one_server.vm.action("terminate-hard",id)
                            if cmd_result == id:
                                return (True, "The VM has been destroyed")
                            else:
                                return (False, cmd_result)
                        print("Waiting to undeploy for destroy")
                        time.sleep(5)
            else:
                return (False, vm)
        else:
            print("Force shutdown")
            cmd_result = self.one_server.vm.action("terminate-hard",id)
            if cmd_result == id:
                return (True, "The VM has been destroyed")
            else:
                return (False, cmd_result)

regex = re.compile(
        r'^(?:http|)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

###################################################################################################

def exception_handler(exception_type, exception, traceback):
    #print "%s: %s" % (exception_type.__name__, exception)
    print("%s" % exception)

if __name__ == "__main__":
    debug = 0
    # if not debug it uses custom exception hook
    if not debug:
        sys.excepthook = exception_handler

    parser = argparse.ArgumentParser(description='PyONE CLI - Copyright (GNU GPL v3) 2019 https://github.com/aramcap/pyone_cli')
    subparsers = parser.add_subparsers(help='Subcommands', dest="command")

    # Menu Token
    parser_token = subparsers.add_parser('token', help='Manage user token')
    subparser_token = parser_token.add_subparsers(help='Token subcommands', dest="command_token")
    ## Menu Token/Create
    subparser_token_create = subparser_token.add_parser('create', help='Set user token')
    subparser_token_create.add_argument('--uri', action='store', help='Open Nebula API URI (i.e. http://cloud.com:2633)')
    subparser_token_create.add_argument('--user', action='store', help='Open Nebula user')
    subparser_token_create.add_argument('--timeout', metavar='int', action='store', help='Set session timeout, default 3600s')
    ## Menu Token/Delete
    subparser_token_delete = subparser_token.add_parser('delete', help='Delete user token')

    # Menu VM
    parser_vm = subparsers.add_parser('vm', help='Manage VMs')
    subparser_vm = parser_vm.add_subparsers(help='VM subcommands', dest="command_vm")
    ## Menu vm/list
    subparser_vm_list = subparser_vm.add_parser('list', help='VMs list')
    ## Menu vm/info
    subparser_vm_info = subparser_vm.add_parser('info', help='VM info')
    subparser_vm_info.add_argument('--id', help='VM ID', required=True)
    ## Menu vm/create
    subparser_vm_create = subparser_vm.add_parser('create', help='Create VM')
    subparser_vm_create.add_argument('--dict', help='Dict with VM specs', required=True)
    ## Menu vm/destroy
    subparser_vm_destroy = subparser_vm.add_parser('destroy', help='Destroy VM')
    subparser_vm_destroy.add_argument('--id', help='VM ID', required=True)
    ## Menu vm/start
    subparser_vm_start = subparser_vm.add_parser('start', help='Start VM')
    subparser_vm_start.add_argument('--id', help='VM ID. Can be a list comma separated', required=True)
    ## Menu vm/stop
    subparser_vm_stop = subparser_vm.add_parser('stop', help='Stop VM')
    subparser_vm_stop.add_argument('--id', help='VM ID. Can be a list comma separated', required=True)

    # Menu Template
    parser_template = subparsers.add_parser('template', help='Manage templates')
    subparser_template = parser_template.add_subparsers(help='Template subcommands', dest="command_template")
    ## Menu template/list
    subparser_template_list = subparser_template.add_parser('list', help='Templates list')
    ## Menu template/info
    subparser_template_info = subparser_template.add_parser('info', help='Template info')
    subparser_template_info.add_argument('--id', help='VM ID', required=True)

    args = parser.parse_args()

    # launch program
    try:
        if args.command == "token":
            if args.command_token == "create":
                uri = args.uri
                user = args.user
                if args.timeout != None:
                    try:
                        timeout = int(args.timeout)
                    except ValueError:
                        subparser_token_create.print_help()
                        sys.exit(2)
                else:
                    timeout = args.timeout
                status,payload = Token.token_set(token_file, uri, user, timeout)
                print(payload)
                exit=0
            elif args.command_token == "delete":
                status,payload = Token.token_del(token_file)
                print(payload)
                exit=0
            else:
                parser_token.print_help()
                sys.exit(2)
        elif args.command == "vm":
            if args.command_vm == "list":
                status,payload = Token.token_get(token_file)
                if status:
                    token = payload
                    status,payload = one(token).get_vms()
                    if status:
                        print("List of VMs")
                        for vm in payload:
                            print(str(vm.ID) + " " + vm.NAME + " " + STATE[str(vm.STATE)])
                        exit=0
                    else:
                        print("ERROR GETTING INFO OF VMS")
                        exit=1
                else:
                    print(payload)
                    exit=0
            elif args.command_vm == "info":
                if not args.id == None:
                    try:
                        id = int(args.id)
                    except ValueError:
                        raise Exception("Input param is not a integer")

                    status,payload = Token.token_get(token_file)
                    if status:
                        token = payload
                        status,payload = one(token).get_vm(id)
                        if status:
                            print("VM info")

                            print()
                            print("ID: "+str(payload.ID))
                            print("NAME: "+ payload.NAME)
                            print("STATE: " + STATE[str(payload.STATE)])
                            print("CPU: " + payload.TEMPLATE["CPU"])
                            print("vCPU: " + payload.TEMPLATE["VCPU"])
                            print("MEMORY: " + payload.TEMPLATE["MEMORY"])
                            if "NIC" in payload.TEMPLATE:
                                print("NIC: " + payload.TEMPLATE["NIC"]["IP"] + " " + payload.TEMPLATE["NIC"]["MAC"] + " " + payload.TEMPLATE["NIC"]["NETWORK"])
                            if "TEMPLATE_ID" in payload.TEMPLATE:
                                print("TEMPLATE_ID: " + payload.TEMPLATE["TEMPLATE_ID"])
                            print("USER: " + payload.UNAME)
                            print("GROUP: " + payload.GNAME)
                            if "HYPERVISOR" in payload.TEMPLATE:
                                print("HYPERVISOR: " + payload.USER_TEMPLATE["HYPERVISOR"])
                        else:
                            print(payload)
                    else:
                        print(payload)
                    exit=0
                else:
                    subparser_vm_info.print_help()
                    sys.exit(2)
            elif  args.command_vm == "create":
                if not args.dict == None:
                    if not isinstance(args.dict, str):
                        raise Exception("Input param is not a dict in string")

                    status,payload = Token.token_get(token_file)
                    if status:
                        token = payload
                        specs = ast.literal_eval(args.dict)
                        if 'TEMPLATE_ID' in specs:
                            template_id = specs['TEMPLATE_ID']
                            specs.pop('TEMPLATE_ID')
                            vm_name = specs['NAME']
                            specs.pop('NAME')
                            cmd_result = one(token).vm_create_template(template_id, specs, vm_name)
                            if isinstance(cmd_result, int):
                                print("VM created with ID: "+str(cmd_result))
                            else:
                                print("ERROR CREATING VM:\n"+cmd_result)
                        else:
                            cmd_result = one(token).vm_create(specs)
                            if isinstance(cmd_result, int):
                                print("VM created with ID: "+str(cmd_result))
                            else:
                                print("ERROR CREATING VM:\n"+cmd_result)
                        exit=0
                    else:
                        print(payload)
                else:
                    subparser_vm_create.print_help()
                    sys.exit(2)
            elif args.command_vm == "destroy":
                if not args.id == None:
                    try:
                        id = int(args.id)
                    except ValueError:
                        raise Exception("Input param is not a integer")

                    status,payload = Token.token_get(token_file)
                    if status:
                        token = payload
                        prompt = input("Are you sure of destroy VM "+str(id)+"? (y/n)")
                        if prompt == "n":
                            exit()
                        elif prompt != "n" and prompt != "y":
                            raise Exception("Input param is not y/n")
                        
                        status, payload = one(token).vm_destroy(id)
                        print(payload)
                        exit=0
                    else:
                        print(payload)
                else:
                    subparser_vm_destroy.print_help()
                    sys.exit(2)
            elif args.command_vm == "start":
                if not args.id == None:
                    try:
                        list_id = args.id.split(",")
                        for elem in list_id:
                            list_id[list_id.index(elem)] = int(elem)
                    except ValueError:
                        raise Exception("Input param is not a integer or integer list")

                    status,payload = Token.token_get(token_file)
                    if status:
                        token = payload
                        for id in list_id:
                            status,payload = one(token).vm_start(id)
                            print(payload)
                        
                        exit=0
                    else:
                        print(payload)
                else:
                    subparser_vm_start.print_help()
                    sys.exit(2)
            elif args.command_vm == "stop":
                if not args.id == None:
                    try:
                        list_id = args.id.split(",")
                        for elem in list_id:
                            list_id[list_id.index(elem)] = int(elem)
                    except ValueError:
                        raise Exception("Input param is not a integer or integer list")
                    
                    status,payload = Token.token_get(token_file)
                    if status:
                        token = payload
                        for id in list_id:
                            status,payload = one(token).vm_stop(id)
                            print(payload)
                        exit=0
                    else:
                        print(payload)
                else:
                    subparser_vm_stop.print_help()
                    sys.exit(2)
            else:
                parser_vm.print_help()
                sys.exit(2)
        elif args.command == "template":
            if args.command_template == "list":
                status,payload = Token.token_get(token_file)
                if status:
                    token = payload
                    status,payload = one(token).get_templates()
                    if status:
                        print("List of Templates")
                        for template in payload:
                            print(str(template.ID) + " " + template.NAME)
                        exit=0
                    else:
                        print("ERROR GETTING INFO OF TEMPLATES")
                else:
                    print(payload)
                    exit=0
            elif args.command_template == "info":
                if not args.id == None:
                    try:
                        id = int(args.id)
                    except ValueError:
                        raise Exception("Input param is not a integer")

                    status,payload = Token.token_get(token_file)
                    if status:
                        token = payload
                        status,payload = one(token).get_template(id)
                        if status:
                            print("Template info")

                            print()
                            print("ID: "+str(payload.ID))
                            print("NAME: "+ payload.NAME)
                            if "CPU" in payload.TEMPLATE:
                                print("CPU: " + payload.TEMPLATE["CPU"])
                            if "VCPU" in payload.TEMPLATE:
                                print("vCPU: " + payload.TEMPLATE["VCPU"])
                            if "MEMORY" in payload.TEMPLATE:
                                print("MEMORY: " + payload.TEMPLATE["MEMORY"])
                            if "NIC" in payload.TEMPLATE:
                                print("NIC: " + payload.TEMPLATE["NIC"]["NETWORK"])
                            print("USER: " + payload.UNAME)
                            print("GROUP: " + payload.GNAME)
                            if "HYPERVISOR" in payload.TEMPLATE:
                                print("HYPERVISOR: " + payload.TEMPLATE["HYPERVISOR"])
                        else:
                            print(payload)
                    else:
                        print(payload)
                    exit=0
                else:
                    subparser_vm_info.print_help()
                    sys.exit(2)
            else:
                parser_template.print_help()
                sys.exit(2)
        else:
            parser.print_help()
            exit=2
    except KeyboardInterrupt:
        print("\nFinished execution by user\n")
        exit=1
    except OSError:
        raise
    except:
        raise

    sys.exit(exit)