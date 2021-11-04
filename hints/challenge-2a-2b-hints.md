**Challenge-2a:**
* The **_total number of AOs is equal to the number of MOs_** according to the Linear Combination of Atomic Orbital (LCAO) principle.
* To count the total number of atomic orbitals, you need to _**count the number of atoms**_ for each element and then _multiply the number of AOs per element_ provided by the notebook:
```python
num_ao = {
    'C': 14,
    'H': 2,
    'N': 14,
    'O': 14,
    'S': 18,
}
```

**Challenge-2b:**
* Use the get_property function to get properties from `ElectronicEnergy`. Make sure that the **driver is reduced**.
* [See this tutorial doc on Property framework](https://qiskit.org/documentation/nature/tutorials/08_property_framework.html)
* Try to find out how you can use property framework to get `ParticleNumber`.
* Use the `ParticleNumber` to find out the number of electrons, MO, SO, and number of qubits.
* The number of qubits is the same as the number of spin orbitals which is double the number of MO. Watch the [Qiskit Nature Demo Session with Max Rossmannek](https://www.youtube.com/watch?v=UtMVoGXlz04&t=38s) for more details.
