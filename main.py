'''
Designs do not use constrianed I/O
Therefore they do not target a real dev board
Spit out JSON for easy result aggregation

Configurations of interest:
-yosys, icestorm
-yosys, vpr
-vendor, icecube
-yosys, icecube
-radiant?

Tested with one or two devices
-The largest device (8k)

Designs:
-SoC
-NES?
-LED blinky

Versions tested with
Radiant: 1.0 64-bit for Linux
Icecube: iCEcube2 2017-08 for Linux
'''

import os
import subprocess
import time
import collections
import json
import re
import sys
import glob

class Timed():
    def __init__(self, t, name):
        self.t = t
        self.name = name
        self.start = None

    def __enter__(self):
        self.start = time.time()

    def __exit__(self, type, value, traceback):
        end = time.time()
        self.t.add_runtime(self.name, end - self.start)

# couldn't get icestorm version
# filed https://github.com/cliffordwolf/icestorm/issues/163
def yosys_ver():
    # Yosys 0.7+352 (git sha1 baddb017, clang 3.8.1-24 -fPIC -Os)
    return subprocess.check_output("yosys -V", shell=True, universal_newlines=True).strip()

def default_package(device, package):
    if package is not None:
        return package
    if device in ('up3k', 'up5k'):
        return 'uwg30'
    else:
        return 'ct256'

def canonicalize(fns):
    return [os.path.realpath(fn) for fn in fns]

class Toolchain:
    def __init__(self):
        self.runtimes = collections.OrderedDict()
        self.toolchain = None
        self.verbose = False
        self.cmds = []
        self.strategy = "default"
        self.seed = None
        self.pcf = None

        self.family = None
        self.device = None
        self.package = None

        self.project_name = None
        self.srcs = None
        self.top = None
        self.out_dir = None

        with Timed(self, 'nop'):
            subprocess.check_call("true", shell=True, cwd=self.out_dir)

    def optstr(self):
        ret = ''
        def add(s):
            nonlocal ret

            if ret:
                ret += '_' + s
            else:
                ret = s

        if self.seed:
            add('seed-%08X' % (self.seed,))
        if self.pcf:
            add('pcf')
        return ret

    def add_runtime(self, name, dt):
        self.runtimes[name] = dt

    def design(self):
        ret = self.family + '-' + self.device + '-' + self.package + '_' + self.toolchain + '_' + self.project_name + '_' + self.strategy
        op = self.optstr()
        if op:
            ret += '_' + op
        return ret

    def project(self, name, family, device, package, srcs, top, out_dir=None):
        self.family = family
        self.device = device
        self.package = package

        self.project_name = name
        self.srcs = canonicalize(srcs)
        self.top = top

        if out_dir is None:
            out_dir = "build/" + self.design()
        self.out_dir = out_dir

        if not os.path.exists(out_dir):
            os.mkdir(out_dir)
        print('Writing to %s' % out_dir)

    def cmd(self, cmd, argstr, env=None):
        print("Running: %s %s" % (cmd, argstr))
        self.cmds.append('%s %s' % (cmd, argstr))
        cmd_base = os.path.basename(cmd)
        open("%s/%s.txt" % (self.out_dir, cmd_base), "w").write("Running: %s %s\n\n" % (cmd_base, argstr))
        with Timed(self, cmd_base):
            if self.verbose:
                cmdstr = "(%s %s) |&tee -a %s.txt; (exit $PIPESTATUS )" % (cmd, argstr, cmd)
                print("Running: %s" % cmdstr)
                print("  cwd: %s" % self.out_dir)
            else:
                cmdstr = "(%s %s) >& %s.txt" % (cmd, argstr, cmd_base)
            subprocess.check_call(cmdstr, shell=True, executable='bash', cwd=self.out_dir, env=env)

    def write_metadata(self):
        out_dir = self.out_dir
        resources = self.resources()
        max_freq = self.max_freq()
        j = {
            'design': self.design(),
            'family': self.family,
            'device': self.device,
            'package': self.package,
            'project': self.project_name,
            'optstr': self.optstr(),
            'seed': self.seed,

            'toolchain': self.toolchain,
            'strategy': self.strategy,
    
            # canonicalize
            'sources': [x.replace(os.getcwd(), '.') for x in self.srcs],
            'top': self.top,
    
            "runtime": self.runtimes,
            "max_freq": max_freq,
            "resources": resources,
            "verions": self.versions(),
            }
        json.dump(j, open(out_dir + '/meta.json', 'w'), sort_keys=True, indent=4)

        # write .csv for easy import
        csv = open(out_dir + '/meta.csv', 'w')
        csv.write('Family,Device,Package,Project,Toolchain,Strategy,option,Freq (MHz),Build (sec),#LUT,#DFF,#BRAM,#CARRY,#GLB,#PLL,#IOB\n')
        seed_str = '%08X' % self.seed if self.seed else ''
        fields = [self.family, self.device, self.package, self.project_name, self.toolchain, self.strategy, seed_str, '%0.1f' % (max_freq/1e6), '%0.1f' % self.runtimes['bit-all']]
        fields += [str(resources[x]) for x in ('LUT', 'DFF', 'BRAM', 'CARRY', 'GLB', 'PLL', 'IOB')]
        csv.write(','.join(fields) + '\n')
        csv.close()

        # Provide some context when comparing runtimes against systems
        subprocess.check_call('uname -a >uname.txt', shell=True, executable='bash', cwd=self.out_dir)
        subprocess.check_call('lscpu >lscpu.txt', shell=True, executable='bash', cwd=self.out_dir)

def icetime_parse(f):
    ret = {
        }
    for l in f:
        # Total path delay: 8.05 ns (124.28 MHz)
        m = re.match(r'Total path delay: .*s \((.*) (.*)\)', l)
        if m:
            assert m.group(2) == 'MHz'
            ret['max_freq'] = float(m.group(1)) * 1e6
    return ret

def icebox_stat(fn, out_dir):
    subprocess.check_call("icebox_stat %s >icebox_stat.txt" % fn, shell=True, cwd=out_dir)
    '''
    DFFs:     22
    LUTs:     24
    CARRYs:   20
    BRAMs:     0
    IOBs:      4
    PLLs:      0
    GLBs:      1
    '''
    ret = {}
    for l in open(out_dir + "/icebox_stat.txt"):
        # DFFs:     22
        m = re.match(r'(.*)s: *([0-9]*)', l)
        t = m.group(1)
        n = int(m.group(2))
        ret[t] = n
    assert 'LUT' in ret
    return ret


class Arachne(Toolchain):
    def __init__(self):
        Toolchain.__init__(self)
        self.toolchain = 'arachne'

    def yosys(self):
        yscript = "synth_ice40 -top %s -blif my.blif" % self.top
        self.cmd("yosys", "-p '%s' %s" % (yscript, ' '.join(self.srcs)))

    def device_simple(self):
        # hx8k => 8k
        assert len(self.device) == 4
        return self.device[2:]

    def run(self):
        with Timed(self, 'bit-all'):
            self.yosys()

            args = ''
            args += "-d " + self.device_simple()
            args += " -P " + self.package
            args += " -o my.asc my.blif"
            if self.seed:
                args += ' --seed %d' % self.seed
            if self.pcf:
                args += ' --pcf-file %s' % self.pcf

            self.cmd("arachne-pnr", args)
            self.cmd("icepack", "my.asc my.bin")

        self.cmd("icetime", "-tmd " + self.device + " my.asc")

    def max_freq(self):
        return icetime_parse(open(self.out_dir + '/icetime.txt'))['max_freq']

    def resources(self):
        return icebox_stat("my.asc", self.out_dir)

    @staticmethod
    def arachne_version():
        '''
        $ arachne-pnr -v
        arachne-pnr 0.1+203+0 (git sha1 7e135ed, g++ 4.8.4-2ubuntu1~14.04.3 -O2)
        '''
        return subprocess.check_output("arachne-pnr -v", shell=True, universal_newlines=True).strip()

    def versions(self):
        return {
            'yosys': yosys_ver(),
            'arachne': Arachne.arachne_version(),
            }


# FIXME: project name still settling ("nextpnr")
class SPNR(Toolchain):
    def __init__(self):
        Toolchain.__init__(self)
        self.toolchain = 'spnr'

    def yosys(self):
        yscript = "synth_ice40 -top %s -nocarry ; write_json my.json" % self.top
        self.cmd("yosys", "-p '%s' %s" % (yscript, ' '.join(self.srcs)))

    def device_simple(self):
        # hx8k => 8k
        assert len(self.device) == 4
        return self.device[2:]

    def run(self):
        '''
         - Run `yosys blinky.ys` in `ice40/` to synthesise the blinky design and  produce `blinky.json`.
            $ cat blinky.ys 
            read_verilog blinky.v
            synth_ice40 -top blinky -nocarry
            write_json blinky.json
         - To place-and-route the blinky using nextpnr, run `./nextpnr-ice40 --hx1k --json ice40/blinky.json --pcf ice40/blinky.pcf --asc blinky.asc`
        '''
        with Timed(self, 'bit-all'):
            self.yosys()

            args = ''
            args += " --" + self.device
            args += " --package " + self.package
            if self.seed:
                args += " --seed " + self.seed
            if self.pcf:
                args += " --pcf " + self.pcf
            args += " --json my.json"
            args += " --asc my.asc"
            self.cmd("nextpnr-ice40", args)
            self.cmd("icepack", "my.asc my.bin")

        self.cmd("icetime", "-tmd " + self.device + " my.asc")

    def max_freq(self):
        return icetime_parse(open(self.out_dir + '/icetime.txt'))['max_freq']

    def resources(self):
        return icebox_stat("my.asc", self.out_dir)

    @staticmethod
    def spnr_version():
        '''
        $ nextpnr-ice40 -V
        nextpnr-ice40 -- Next Generation Place and Route (git sha1 edf7bd0)
        $ echo $?
        1
        '''
        return subprocess.check_output("nextpnr-ice40 -V || true", shell=True, universal_newlines=True).strip()

    def versions(self):
        return {
            'yosys': yosys_ver(),
            'nextpnr-ice40': SPNR.spnr_version(),
            }


class VPR(Toolchain):
    def __init__(self):
        Toolchain.__init__(self)
        self.toolchain = 'vpr'

    def yosys(self):
        yscript = "synth_ice40 -top %s -nocarry; ice40_opt -unlut; abc -lut 4; opt_clean; write_blif -attr -cname -param my.eblif" % self.top
        self.cmd("yosys", "-p '%s' %s" % (yscript, ' '.join(self.srcs)))

    def sfad_dir(self):
        return os.getenv("SFAD_DIR", os.getenv("HOME") + "/symbiflow-arch-defs")

    def sfad_build(self):
        sfad_build = os.getenv("SFAD_BUILD", None)
        if sfad_build:
            return sfad_build

        return self.sfad_dir() + "/tests/build/ice40-top-routing-virt-" + self.device

    def run(self):
        self.sfad_build = self.sfad_build()
        if not os.path.exists(self.sfad_build):
            raise Exception("Missing VPR dir: %s" % self.sfad_build)

        with Timed(self, 'bit-all'):
            self.yosys()

            arch_xml = self.sfad_build + '/arch.xml'
            rr_graph = self.sfad_build + "/rr_graph.real.xml"
            # --fix_pins " + io_place
            #io_place = ".../symbiflow-arch-defs/tests/ice40/tiny-b2_blink//build-ice40-top-routing-virt-hx8k/io.place"
            #devstr = "hx8k-cm81"
            devstr = self.device + '-' + self.package

            optstr = ''
            if self.seed:
                optstr += ' --seed %d' % self.seed
            if self.pcf:
                #io_place_file = self.out_dir + '/io.place'
                #create_ioplace = 'python3 ' + self.sfad_dir() + '/ice40/utils/ice40_create_ioplace.py'
                create_ioplace = self.sfad_dir() + '/ice40/utils/ice40_create_ioplace.py'
                map_file = self.sfad_dir() + '/ice40/devices/layouts/icebox/%s.%s.pinmap.csv' % (self.device, self.package)
                self.cmd(create_ioplace, '--pcf %s --blif %s --map %s --output %s' % (self.pcf, "my.eblif", map_file, 'io.place'))
                optstr += ' --fix_pins io.place'

            self.cmd("vpr", arch_xml + " my.eblif --device " + devstr + " --min_route_chan_width_hint 100 --route_chan_width 100 --read_rr_graph " + rr_graph + " --pack --place --route" + optstr)

            self.cmd("icebox_hlc2asc", "top.hlc > my.asc")
            self.cmd("icepack", "my.asc my.bin")

        self.cmd("icetime", "-tmd " + self.device + " my.asc")

    def max_freq(self):
        return icetime_parse(open(self.out_dir + '/icetime.txt'))['max_freq']

    """
    @staticmethod
    def resource_parse(f):
        '''
        abanonded in favor of icebox_stat
        although maybe would be good to compare results?

        Resource usage...
            Netlist      0    blocks of type: EMPTY
            Architecture 0    blocks of type: EMPTY
            Netlist      4    blocks of type: BLK_TL-PLB
            Architecture 960    blocks of type: BLK_TL-PLB
            Netlist      0    blocks of type: BLK_TL-RAM
            Architecture 32    blocks of type: BLK_TL-RAM
            Netlist      2    blocks of type: BLK_TL-PIO
            Architecture 256    blocks of type: BLK_TL-PIO

        Device Utilization: 0.00 (target 1.00)
            Block Utilization: 0.00 Type: EMPTY
            Block Utilization: 0.00 Type: BLK_TL-PLB
            Block Utilization: 0.00 Type: BLK_TL-RAM
            Block Utilization: 0.01 Type: BLK_TL-PIO
        '''
        def waitfor(s):
            while True:
                l = f.readline()
                if not l:
                    raise Exception("EOF")
                if s.find(s) >= 0:
                    return
        waitfor('Resource usage...')
        while True:
            l = f.readline().strip()
            if not l:
                break
            # Netlist      2    blocks of type: BLK_TL-PIO
            # Architecture 256    blocks of type: BLK_TL-PIO
            parts = l.split()
            if parts[0] != 'Netlist':
                continue

        waitfor('Device Utilization: ')
    """

    def resources(self):
        return icebox_stat("my.asc", self.out_dir)

    @staticmethod
    def vpr_version():
        '''
        vpr  --version

        VPR FPGA Placement and Routing.
        Version: 8.0.0-dev+vpr-7.0.5-6027-g94a747729
        Revision: vpr-7.0.5-6027-g94a747729
        Compiled: 2018-06-21T16:45:11 (release build)
        Compiler: GNU 6.3.0 on Linux-4.9.0-5-amd64 x86_64
        University of Toronto
        vtr-users@googlegroups.com
        This is free open source code under MIT license.
        '''
        out = subprocess.check_output("vpr --version", shell=True, universal_newlines=True).strip()
        version = None
        revision = None
        for l in out.split('\n'):
            l = l.strip()
            if l.find('Version:') == 0:
                version = l
            if l.find('Revision:') == 0:
                revision = l
        assert version is not None
        assert revision is not None
        return version + ', ' + revision

    def versions(self):
        return {
            'yosys': yosys_ver(),
            'vpr': VPR.vpr_version(),
            }


# no seed support?
class Icecube2(Toolchain):
    def __init__(self):
        Toolchain.__init__(self)
        self.icecubedir = os.getenv("ICECUBEDIR", "/opt/lscc/iCEcube2.2017.08")

    def run(self):
        with Timed(self, 'bit-all'):
            print('top: %s' % self.top)
            env = os.environ.copy()
            env["SRCS"] = ' '.join(self.srcs)
            env["TOP"] = self.top
            env["ICECUBEDIR"] = self.icecubedir
            #env["ICEDEV"] = 'hx8k-ct256'
            env["ICEDEV"] = self.device + '-' + self.package
            self.cmd("../../icecubed.sh", "--syn %s --strategy %s" % (self.syn(), self.strategy), env=env)

            self.cmd("iceunpack", "my.bin my.asc")

        self.cmd("icetime", "-tmd hx8k my.asc")

    def max_freq(self):
        return icetime_parse(open(self.out_dir + '/icetime.txt'))['max_freq']

    def resources(self):
        return icebox_stat("my.asc", self.out_dir)

    @staticmethod
    def asc_ver(f):
        '''
        .comment
        Lattice
        iCEcube2 2017.08.27940
        Part: iCE40HX1K-TQ144
        Date: Jun 27 2018 13:22:06
        '''
        for l in f:
            if l.find('iCEcube2') == 0:
                return l.split()[1].strip()
        assert 0

    def versions(self):
        return {
            'yosys': yosys_ver(),
            'icecube2': Icecube2.asc_ver(open(self.out_dir + '/my.asc')),
            }


class Icecube2Synpro(Icecube2):
    def __init__(self):
        Icecube2.__init__(self)
        self.toolchain = 'icecube2-synpro'

    def syn(self):
        return "synpro"


class Icecube2LSE(Icecube2):
    def __init__(self):
        Icecube2.__init__(self)
        self.toolchain = 'icecube2-lse'

    def syn(self):
        return "lse"


class Icecube2Yosys(Icecube2):
    def __init__(self):
        Icecube2.__init__(self)
        self.toolchain = 'icecube2-yosys'

    def syn(self):
        return "yosys-synpro"


# .asc version field just says "DiamondNG"
# guess that was the code name...
# no seed support? -n just does more passes
class Radiant(Toolchain):
    def __init__(self):
        Toolchain.__init__(self)
        self.radiantdir = os.getenv("RADIANTDIR", "/opt/lscc/radiant/1.0")

    def run(self):
        # acceptable for either device
        assert (self.device, self.package) in [('up3k', 'uwg30'), ('up5k', 'uwg30'), ('up5k', 'sg48')]
        # FIXME: strategy doesn't seem to actually do anything
        # any value can be passed in, and valid values seem to get ignored
        #assert self.strategy in ['default', 'Quick', 'Timing', 'Area']

        with Timed(self, 'bit-all'):
            env = os.environ.copy()
            env["SRCS"] = ' '.join(self.srcs)
            env["TOP"] = self.top
            env["RADIANTDIR"] = self.radiantdir
            env["RADDEV"] = self.device + '-' + self.package
            syn = self.syn()
            self.cmd("../../radiant.sh", "--syn %s --strategy %s" % (syn, self.strategy), env=env)

            self.cmd("iceunpack", "my.bin my.asc")

        self.cmd("icetime", "-tmd up5k my.asc")

    def max_freq(self):
        return icetime_parse(open(self.out_dir + '/icetime.txt'))['max_freq']

    def resources(self):
        return icebox_stat("my.asc", self.out_dir)

    def radiant_ver(self):
        # a lot of places where this is, but not sure whats authoritative
        for l in open(self.radiantdir + '/data/ispsys.ini'):
            # ./data/ispsys.ini:19:ProductType=1.0.0.350.6
            if l.find('ProductType') == 0:
                return l.split('=')[1].strip()
        assert 0

    def versions(self):
        return {
            'yosys': yosys_ver(),
            'radiant': self.radiant_ver(),
            }


class RadiantLSE(Radiant):
    def __init__(self):
        Radiant.__init__(self)
        self.toolchain = 'radiant-lse'

    def syn(self):
        return "lse"


class RadiantSynpro(Radiant):
    def __init__(self):
        Radiant.__init__(self)
        self.toolchain = 'radiant-synpro'

    def syn(self):
        return "synplify"


# @E: CG389 :"/home/mcmaster/.../impl/impl.v":18:4:18:7|Reference to undefined module SB_LUT4
# didn't look into importing edif
class RadiantYosys(Radiant):
    def __init__(self):
        Radiant.__init__(self)
        self.toolchain = 'radiant-yosys'

    def syn(self):
        return "yosys-synpro"

def print_stats(t):
    print('Design %s' % t.design())
    print('  Family: %s' % t.family)
    print('  Device: %s' % t.device)
    print('  Package: %s' % t.package)
    print('  Project: %s' % t.project_name)
    print('  Toolchain: %s' % t.toolchain)
    print('  Strategy: %s' % t.strategy)
    if t.seed:
        print('  Seed: 0x%08X (%u)' % (t.seed, t.seed))
    else:
        print('  Seed: default')
    print('Timing:')
    for k, v in t.runtimes.items():
        print('  % -16s %0.3f' % (k + ':', v))
    print('Max frequency: %0.3f MHz' % (t.max_freq() / 1e6,))
    print('Resource utilization')
    for k, v in sorted(t.resources().items()):
        print('  %- 20s %s' % (k + ':', v))

toolchains = {
        'arachne': Arachne,
        'vpr': VPR,
        'spnr': SPNR,
        'icecube2-synpro':  Icecube2Synpro,
        'icecube2-lse':     Icecube2LSE,
        'icecube2-yosys':   Icecube2Yosys,
        'radiant-synpro':   RadiantSynpro,
        'radiant-lse':      RadiantLSE,
        #'radiant-yosys':    RadiantYosys,
        #'radiant': VPR,
        }

def run(family, device, package, toolchain, project, out_dir=None, verbose=False, strategy="default", seed=None, pcf=None):
    assert family == 'ice40'
    #assert device == 'hx8k'
    #assert package == 'ct256'
    package = default_package(device, package)

    t = toolchains[toolchain]()
    t.verbose = verbose
    t.strategy = strategy
    t.seed = seed
    # XXX: sloppy path handling here...
    t.pcf = os.path.realpath(pcf) if pcf else None

    if not os.path.exists("build"):
        os.mkdir("build")

    t.project(project['name'], family, device, package, project['srcs'], project['top'], out_dir)

    t.run()
    print_stats(t)
    t.write_metadata()

def list_toolchains():
    print('Supported toolchains:')
    for t in sorted(toolchains.keys()):
        print(t)

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description=
        'Analyze tool runtimes'
    )

    parser.add_argument('--verbose', action='store_true', help='')
    parser.add_argument('--overwrite', action='store_true', help='')
    parser.add_argument('--family', default='ice40', help='Device family')
    parser.add_argument('--device', default='hx8k', help='Device within family')
    parser.add_argument('--package', default=None, help='Device package')
    parser.add_argument('--strategy', default='default', help='Optimization strategy')
    parser.add_argument('--toolchain', help='Tools to use')
    parser.add_argument('--list-toolchains', action='store_true', help='')
    parser.add_argument('--project', help='Source code to run on')
    parser.add_argument('--seed', default=None, help='32 bit sSeed number to use, possibly directly mapped to PnR tool')
    parser.add_argument('--out-dir', default=None, help='Output directory')
    parser.add_argument('--pcf', default=None, help='')
    args = parser.parse_args()

    if args.list_toolchains:
        list_toolchains()
    else:
        assert args.toolchain is not None, 'toolchain required'
        assert args.project is not None, 'project required'

        project_fn = 'project/' + args.project + '.json'
        seed = int(args.seed, 0) if args.seed else None
        run(args.family, args.device, args.package, args.toolchain, json.load(open(project_fn, 'r')), args.out_dir, strategy=args.strategy, seed=seed, verbose=args.verbose, pcf=args.pcf)

if __name__ == '__main__':
    main()
