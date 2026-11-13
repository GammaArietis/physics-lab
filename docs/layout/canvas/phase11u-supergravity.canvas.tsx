import {
  Callout,
  Card,
  CardBody,
  CardHeader,
  Divider,
  Grid,
  H1,
  H2,
  Pill,
  Row,
  Stack,
  Stat,
  Table,
  Text,
} from "cursor/canvas";

export default function Phase11USupergravity() {
  return (
    <Stack gap={24}>
      <Stack gap={8}>
        <H1>Supergravity as input</H1>
        <Text tone="secondary">
          Phase 11U couples rigid N=1 SUSY to the existing gravity family only
          after local supersymmetry is authorized as a new physical input.
          Rigid SUSY is not local SUSY. Source: phase11u-supergravity-v1 ·
          HUMAN-SUGRA-AUTHORIZATION-v1 · old-minimal TEST EXTENSION · frozen
          4C c26df583… · 2026-09-25.
        </Text>
        <Row gap={8} wrap>
          <Pill active>NEW PHYSICAL INPUT</Pill>
          <Pill tone="warning" active>
            UNIQUE_THEORY NOT_DERIVED
          </Pill>
          <Pill active>c0 + c1 R unchanged</Pill>
          <Pill tone="neutral" active>
            quantum UNTESTED
          </Pill>
        </Row>
      </Stack>

      <Callout tone="warning" title="Localizing epsilon is not a rewrite of 4C">
        Under the authorized supergravity input, epsilon becomes epsilon(x) and
        the old-minimal multiplet (vierbein, gravitino, S, P, A_mu) is required.
        Replacing a partial derivative by a covariant derivative is not
        supergravity. Frozen S_gravity = integral sqrt(-g)(c0 + c1 R) was not
        rewritten.
      </Callout>

      <Grid columns={4} gap={12}>
        <Stat value="ABSENT" label="coverage before 11U" />
        <Stat value="VERIFIED" label="old-minimal multiplet / gravitino" />
        <Stat value="0" label="new PFR / new parameter count" />
        <Stat value="2" label="free functions remaining (W, K)" />
      </Grid>

      <H2>Coverage after the input</H2>
      <Table
        headers={["ingredient", "status", "what was shown"]}
        rows={[
          ["local SUSY algebra", "PARTIAL", "epsilon(x) remainder; nabla-only is not SUGRA"],
          ["old-minimal multiplet", "VERIFIED", "e_mu^a, psi_mu, S, P, A_mu; 6+6 off shell"],
          ["local transformations", "PARTIAL", "not implemented on frozen 4C"],
          ["off-shell closure", "PARTIAL", "DOF match; full commutator untested"],
          ["invariant action", "PARTIAL", "4C not replaced by a canonical SUGRA action"],
          ["chiral / vector coupling", "PARTIAL", "possible; K and W not unique"],
          ["F-term potential", "VERIFIED", "V_sugra = e^K (|DW|^2 minus 3 |W|^2)"],
          ["D-term structure", "PARTIAL", "mixes with Kaehler; g still free"],
          ["super-Higgs", "PARTIAL", "needs a demonstrated broken vacuum"],
          ["gravitino mass", "PARAMETER-DEPENDENT", "schematic e^{K/2} |W|; no number"],
          ["quantum SUGRA", "UNTESTED", "classical invariance is not unitarity"],
        ]}
        striped
        rowTone={[
          "warning",
          "success",
          "warning",
          "warning",
          "warning",
          "warning",
          "success",
          "warning",
          "warning",
          "neutral",
          "neutral",
        ]}
      />

      <H2>Vacuum branches, none selected</H2>
      <Table
        headers={["branch", "SUSY", "vacuum energy", "gravitino mass", "unique?"]}
        rows={[
          ["AdS-like", "preserving", "negative if W ≠ 0", "PARAMETER-DEPENDENT", "no"],
          ["Minkowski-like", "preserving", "zero only if W = 0 too", "vanishes if W = 0", "no"],
          ["breaking family", "breaking", "sign not selected", "PARAMETER-DEPENDENT", "no"],
        ]}
        striped
      />

      <Grid columns={2} gap={16}>
        <Card>
          <CardHeader>Derived given the input</CardHeader>
          <CardBody>
            <Stack gap={8}>
              <Text>
                Rigid V_F = |W_phi|^2 does not survive. F-flatness is not a
                Minkowski vacuum: V becomes minus 3 e^K |W|^2 when DW = 0.
              </Text>
              <Text>
                The 11T rigid soft term is not automatically a consistent
                supergravity soft term. Compatibility requires additional
                structure.
              </Text>
            </Stack>
          </CardBody>
        </Card>
        <Card>
          <CardHeader>Still free / still PARTIAL</CardHeader>
          <CardBody>
            <Stack gap={8}>
              <Text>c0, c1, lambda_a, lambda_b, gauge coupling, FI parameter.</Text>
              <Text>Holomorphic W and Kaehler K remain free functions.</Text>
              <Text>
                Vacuum selection NOT_FOUND. UV PROPERTY NOT FOUND. Global
                gauge PARTIAL. Quantum supergravity UNTESTED.
              </Text>
            </Stack>
          </CardBody>
        </Card>
      </Grid>

      <Divider />
      <Text tone="secondary">
        Hierarchy kept: rigid SUSY ≠ local SUSY ≠ unique vacuum. Super-Higgs
        ≠ unique breaking mechanism. Supergravity ≠ UV completion. No
        strings, mediation, or experimental Planck/gravitino values. New PFR
        count: 0.
      </Text>
    </Stack>
  );
}
