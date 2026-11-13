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

export default function Phase11AADirectMediation() {
  return (
    <Stack gap={24}>
      <Stack gap={8}>
        <H1>Direct mediation as input</H1>
        <Text tone="secondary">
          Phase 11AA activates only direct mediation as a new physical input.
          Hidden X is reused as a declared input, not as a derivation. Source:
          phase11aa-direct-mediation-v1 · HUMAN-SUSY-MEDIATION-DIRECT-AUTHORIZATION-v1
          · M_direct INPUT · operators O_W, O_K · frozen 4C c26df583… · 2026-09-25.
        </Text>
        <Row gap={8} wrap>
          <Pill active>NEW PHYSICAL INPUT</Pill>
          <Pill tone="warning" active>
            UNIQUENESS NOT_DERIVED
          </Pill>
          <Pill active>X reused, M_direct new</Pill>
          <Pill tone="neutral" active>
            PHASE_11AA_STOPPED
          </Pill>
        </Row>
      </Stack>

      <Callout tone="warning" title="A hidden F-term is not a direct channel">
        F_X is INPUT and is not identified with F_phi, F_T, or gravitino mass.
        Communication is encoded in effective operators O_W and O_K. No
        messengers, no modulus, no compensator, no mixed mediation. Gauge
        coupling remains FREE.
      </Callout>

      <Grid columns={4} gap={12}>
        <Stat value="ABSENT" label="coverage before 11AA" />
        <Stat value="3" label="new parameters (M_direct, c_W, c_K)" />
        <Stat value="INPUT" label="mediation scale" />
        <Stat value="NOT_DERIVED" label="direct-mediation uniqueness" />
      </Grid>

      <H2>Declared operators and required statuses</H2>
      <Table
        headers={["status variable", "value", "meaning"]}
        rows={[
          ["DIRECT_MEDIATION_INPUT_STATUS", "VERIFIED", "authorization present and frozen"],
          ["HIDDEN_SECTOR_STATUS", "VERIFIED", "X is REUSED_EXISTING_TEST_FIELD"],
          ["DIRECT_OPERATOR_STATUS", "VERIFIED", "O_W and O_K declared"],
          ["gauge / SUSY / dimension", "VERIFIED", "singlet chiral dim-5; invariant real dim-6"],
          ["DIRECT_GAUGINO_MASS_STATUS", "PARTIAL", "tree-level M_lambda ~ c_W F_X / M_direct"],
          ["DIRECT_SCALAR_SOFT_MASS_STATUS", "PARTIAL", "tree-level m^2 ~ c_K |F_X|^2 / M_direct^2"],
          ["A / B / FI", "UNTESTED", "those operators were not added"],
          ["MEDIATION_SCALE_STATUS", "INPUT", "M_direct not messenger mass, T, or 11V scale"],
          ["ANOMALY_STATUS", "VERIFIED", "no new charged fields"],
          ["SUGRA / vacuum / UV", "PARTIAL / PARTIAL / NOT_FOUND", "no completion, no unique vacuum"],
          ["MODULI_IMPACT_STATUS", "NOT_FOUND", "T not introduced"],
          ["PARAMETER_REDUCTION / PFR", "NONE / NOT_FOUND", "three new parameters, zero PFRs"],
        ]}
        striped
        rowTone={[
          "success",
          "success",
          "success",
          "success",
          "warning",
          "warning",
          "neutral",
          "success",
          "success",
          "warning",
          "neutral",
          "neutral",
        ]}
      />

      <Grid columns={2} gap={16}>
        <Card>
          <CardHeader>Derived given the input</CardHeader>
          <CardBody>
            <Stack gap={8}>
              <Text>
                O_W = int d^2 theta (c_W X / M_direct) W^alpha W_alpha generates
                a tree-level gaugino mass. O_K generates a tree-level scalar
                soft mass. Loop orders are not imported from 11X or 11Y.
              </Text>
              <Text>
                Neither relation is a PFR. c_W, c_K, F_X, and M_direct remain
                free.
              </Text>
            </Stack>
          </CardBody>
        </Card>
        <Card>
          <CardHeader>Isolation and remaining freedom</CardHeader>
          <CardBody>
            <Stack gap={8}>
              <Text>
                Gravity, gauge, anomaly, and modulus mediation previously
                tested, PARTIAL. Documentary comparison only.
              </Text>
              <Text>
                c0, c1, lambda_a, lambda_b, xi, W, K remain free. 11V–11Z hashes
                unchanged. Mixed mediation remains off.
              </Text>
            </Stack>
          </CardBody>
        </Card>
      </Grid>

      <Divider />
      <Text tone="secondary">
        Hierarchy kept: hidden X ≠ direct mediation. F_X ≠ F_phi ≠ F_T.
        Direct operators ≠ gravity mediation ≠ gauge mediation. PHASE_11AA_STOPPED
        = TRUE. Next phase requires a separate authorization.
      </Text>
    </Stack>
  );
}
