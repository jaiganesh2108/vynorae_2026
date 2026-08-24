from qiskit import QuantumCircuit
from qiskit_aer import Aer
from qiskit.visualization import plot_histogram

qc = QuantumCircuit(1, 1)
qc.h(0)
qc.measure(0, 0)
print(qc.draw())

simulator = Aer.get_backend("qasm_simulator")
job = simulator.run(qc, shots=1000)

result = job.result()
counts = result.get_counts()
print("Result:", counts)

"""
Output:

     ┌───┐┌─┐
  q: ┤ H ├┤M├
     └───┘└╥┘
c: 1/══════╩═
           0 

Result: {'1': 499, '0': 501}    
"""