import pyone, time, getpass

one_uri = "http://cloud.local:2633"
user = "aramcap"
token = "***"

def server(one_session):
    return pyone.OneServer(one_uri, session=user+":"+one_session)

## GET ALL VMs
def get_vms():
    one = server(token)
    vmpool = one.vmpool.info(-1,-1,-1,-1)
    return vmpool.VM

## GET VM
def get_vm(id):
    one = server(token)
    vm = one.vm.info(id)
    return vm

## GET ALL TEMPLATES
def get_templates():
    one = server(token)
    templatepool = one.templatepool.info(-1,-1,-1)
    return templatepool.VMTEMPLATE

## GET TEMPLATE
def get_template(id):
    one = server(token)
    template = one.template.info(id)
    return template

## VM START
def vm_start(id):
    one = server(token)
    return (True, one.vm.action("resume",id))

## VM STOP
def vm_stop(id):
    one = server(token)
    return (True, one.vm.action("undeploy",id))

def vm_create(specs):
    one = server(token)
    # first, check if vm name exists
    vms = get_vms()
    for vm in vms:
        if vm.NAME == specs['NAME']:
            return (False, "ERROR: VM NAME EXISTS")

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

    # launch query and return result
    return (True, one.vm.allocate(query))

def vm_create_template(template_id, specs, vm_name=""):
    one = server(token)
    # first, check if vm name exists
    vms = get_vms()
    for vm in vms:
        if vm.NAME == vm_name:
            return (False, "ERROR: VM NAME EXISTS")

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

    # launch query and return result
    return (True, one.template.instantiate(template_id, vm_name, False, query, False))

def vm_destroy(id, force=False):
    one = server(token)
    if not force:
        print("Tidy shutdown")
        vm = get_vm(id)
        if vm.STATE == 9:
            return (True, one.vm.action("terminate-hard",id))
        elif vm.STATE == 6:
            return (False, "The VM has already been destroyed")
        else:
            # first, undeploy
            one.vm.action("undeploy",id)
            while(True):
                # second, check if status is UNDEPLOYED
                vm = get_vm(id)
                if vm.STATE == 9:
                    return (True, one.vm.action("terminate-hard",id))
                print("Waiting to turn off for destroy")
                time.sleep(5)
    else:
        print("Force shutdown")
        return (True, one.vm.action("terminate-hard",id))

def token_get():
    password = getpass.getpass(prompt='Password: ')
    one = server(user+":"+password)
    return one.user.login(user, "", 300, -1)

#print(vm_create({'NAME': 'vm1-aramos', 'CPU': 1, 'VCPU': 2, 'MEMORY': 1024, 'DISK': [{'IMAGE_ID': 55, 'SIZE': 102400}]}))
#print(vm_create_template(31, {'CPU': 1, 'VCPU': 2, 'MEMORY': 1024, 'DISK': [{'IMAGE_ID': 55, 'SIZE': 102400}]}, 'vm1-aramos'))
#print(vm_start(3369))
#print(vm_destroy(3377))
print(get_vms())

#print(token_get())