{
  description = "Prometheus script wrapper";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-25.05";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
      ...
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

      in
      {
        packages = {
          prometheus-script-wrapper = pkgs.python3.pkgs.callPackage ./package.nix { };
          default = self.packages.${system}.prometheus-script-wrapper;
        };

        devShells.default = pkgs.mkShell {
          inputsFrom = [ self.packages.${system}.prometheus-script-wrapper ];
          packages = [
            self.packages.${system}.prometheus-script-wrapper.build-system
            pkgs.uv
            pkgs.python3.pkgs.ruff
            pkgs.python3.pkgs.mypy
            pkgs.python3.pkgs.pytest
          ];
        };

        formatter = pkgs.nixfmt-tree;
      }
    );
}
