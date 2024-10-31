import inductiva

# Instantiate machine group
machine_group = inductiva.resources.MachineGroup('c2-standard-4')
machine_group.start()

# Set simulation input directory
input_dir = inductiva.utils.download_from_url(
    "https://storage.googleapis.com/inductiva-api-demo-files/"
    "reef3d-dambreak-example.zip", unzip=True)

# Initialize the Simulator
reef3d = inductiva.simulators.REEF3D()

# Run simulation with config files in the input directory
task = reef3d.run(input_dir=input_dir, on=machine_group)

task.wait()
task.download_outputs()

machine_group.terminate()
