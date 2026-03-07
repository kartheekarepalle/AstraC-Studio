"""Debug bubble sort step by step."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api'))
from compiler_pipeline import run_pipeline
from compile_run import TACInterpreter
import re

source = r'''
#include <stdio.h>
int main() {
    int arr[5], i, j, temp;
    arr[0] = 64;
    arr[1] = 34;
    arr[2] = 25;
    arr[3] = 12;
    arr[4] = 22;
    for (i = 0; i < 4; i++) {
        for (j = 0; j < 4; j++) {
            if (arr[j] > arr[j+1]) {
                temp = arr[j];
                arr[j] = arr[j+1];
                arr[j+1] = temp;
            }
        }
    }
    for (i = 0; i < 5; i++) {
        printf("%d ", arr[i]);
    }
    printf("\n");
    return 0;
}
'''

result = run_pipeline(source)
tac = result.get('optimized_ir') or result.get('ir') or []
print("TAC:")
for i, l in enumerate(tac):
    print(f"  {i:3d}: {l}")

# Run with debug: patch the interpreter to trace
class DebugInterpreter(TACInterpreter):
    def _exec_func(self, fname, args_map):
        if fname != 'main':
            return super()._exec_func(fname, args_map)
        
        body = self.funcs[fname]['body']
        env = dict(args_map)
        labels = {}
        for i, line in enumerate(body):
            lm = re.match(r'^(L\d+):$', line)
            if lm:
                labels[lm.group(1)] = i

        pc = 0
        step = 0
        while pc < len(body):
            self.steps += 1
            if self.steps > self.MAX_STEPS:
                break
            line = body[pc].strip()
            if not line:
                pc += 1
                continue

            # Debug: print swap operations
            if 'arr [' in line and '= arr' in line:
                step += 1
                if step <= 50:
                    arr = env.get('arr', {})
                    j = env.get('j', '?')
                    print(f"  STEP {step}: pc={pc} line={line!r}  j={j}  arr={dict(sorted(arr.items())) if isinstance(arr, dict) else arr}  temp={env.get('temp','?')}")
            
            # Delegate to parent execution
            result = self._exec_line(line, body, env, labels, pc)
            if result is not None:
                if isinstance(result, tuple):
                    pc = result[0]
                    continue
                return result
            pc += 1
        return 0

    def _exec_line(self, line, body, env, labels, pc):
        """Execute one line, return new pc as tuple, return value, or None to advance."""
        if re.match(r'^L\d+:$', line):
            return None
        dm = re.match(r'^DECL\s+(\w+)$', line)
        if dm:
            env.setdefault(dm.group(1), 0)
            return None
        rm = re.match(r'^RETURN\s*(.*)?$', line)
        if rm:
            val = rm.group(1).strip() if rm.group(1) else ''
            return self._eval(val, env) if val else 0
        gm = re.match(r'^GOTO\s+(L\d+)$', line)
        if gm:
            lbl = gm.group(1)
            if lbl in labels:
                return (labels[lbl],)
            return None
        ifm = re.match(r'^IF_FALSE\s+(.+?)\s+GOTO\s+(L\d+)$', line)
        if ifm:
            cond_val = self._eval(ifm.group(1), env)
            if not cond_val:
                lbl = ifm.group(2)
                if lbl in labels:
                    return (labels[lbl],)
            return None
        cm = re.match(r'^CALL\s+(\w+)\((.*)?\)$', line)
        if cm:
            self._handle_call(cm.group(1), cm.group(2) or '', env)
            return None
        tcm = re.match(r'^(\w+)\s*=\s*CALL\s+(\w+)\((.*)?\)$', line)
        if tcm:
            result = self._handle_call(tcm.group(2), tcm.group(3) or '', env)
            env[tcm.group(1)] = result if result is not None else 0
            return None
        incdec = re.match(r'^(\w+)\s*(\+\+|--)$', line)
        if incdec:
            v = incdec.group(1)
            op = incdec.group(2)
            val = self._resolve(v, env)
            env[v] = val + 1 if op == '++' else val - 1
            return None
        arrs = re.match(r'^(\w+)\s*\[\s*(.+?)\s*\]\s*=\s*(.+)$', line)
        if arrs:
            arr_name = arrs.group(1)
            idx = int(self._eval(arrs.group(2), env))
            val = self._eval(arrs.group(3), env)
            if arr_name not in env or not isinstance(env[arr_name], dict):
                env[arr_name] = {}
            env[arr_name][idx] = val
            return None
        am = re.match(r'^(\w+)\s*=\s*(.+)$', line)
        if am:
            env[am.group(1)] = self._eval(am.group(2).strip(), env)
            return None
        return None

print("\nRunning with debug:")
interp = DebugInterpreter(tac)
rt = interp.run()
print(f"\nOutput: {rt['stdout']!r}")
print(f"Stderr: {rt['stderr']!r}")
