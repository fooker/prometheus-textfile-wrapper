{
  buildPythonApplication,
  hatchling,
  click,
  prometheus-client,
  pytestCheckHook,
  bash,
  ...
}:

buildPythonApplication {
  pname = "prometheus-script-wrapper";
  version = "0.1.0";

  src = ./.;

  pyproject = true;
  build-system = [ hatchling ];

  # Required for test execution
  nativeBuildInputs = [ bash ];

  dependencies = [
    click
    prometheus-client
  ];

  pythonImportsCheck = [ "prometheus_script_wrapper" ];

  doCheck = true;

  nativeCheckInputs = [
    pytestCheckHook
  ];
}
