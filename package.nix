{
  buildPythonApplication,
  hatchling,
  uvicorn,
  fastapi,
  pydantic,
  httpx,
  prometheus-client,
  pytestCheckHook,
  testcontainers,
  ...
}:

buildPythonApplication {
  pname = "prometheus-script-wrapper";
  version = "0.1.0";

  src = ./.;

  pyproject = true;
  build-system = [ hatchling ];

  dependencies =
    [
      prometheus-client
    ];

  pythonImportsCheck = [ "prometheus_script_wrapper" ];

  # Requires running docker instance for testcontianers
  doCheck = true;

  nativeCheckInputs = [
    pytestCheckHook
  ];
}
