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

export default function Phase11YAnomalyMediation() {
  return (
    <Stack gap={24}>
      <Stack gap={8}>
        <H1>Anomaly mediation as input</H1>
        <Text tone="secondary">
          Phase 11Y activates only anomaly mediation as a new physical input.
          Beta functions do not derive it. Source: phase11y-anomaly-mediation-v1
          · HUMAN-SUSY-MEDIATION-ANOMALY-AUTHORIZATION-v1 · compensator F_phi
          INPUT · P5J/P5K REFERENCE_ONLY · frozen 4C c26df583… · 2026-09-25.
        </Text>
        <Row gap={8} wrap>
          <Pill active>NEW PHYSICAL INPUT</Pill>
          <Pill tone="warning" active>
            UNIQUENESS NOT_DERIVED
          </Pill>
          <Pill active>F_phi INPUT, not F_X</Pill>
          <Pill tone="neutral" active>
            PHASE_11Y_STOPPED
          </Pill>
        </Row>
      </Stack>

      <Callout tone="warning" title="A beta function is not a compensator">
        Under the authorized anomaly-mediation input, Phi_C = 1 + theta^2 F_phi
        is required. F_phi is independent of F_X and of any modulus. Soft terms
        use existing laboratory RG objects and stay PARTIAL. Gauge coupling
        remains FREE. No messengers, no modulus mediation, no direct mediation.
      </Callout>

      <Grid columns={4} gap={12}>
        <Stat value="ABSENT" label="coverage before 11Y" />
        <Stat value="1" label="new parameter (F_phi)" />
        <Stat value="FREE" label="gauge coupling constraint" />
        <Stat value="NOT_DERIVED" label="anomaly-mediation uniqueness" />
      </Grid>

      <H2>Required status audit</H2>
      <Table
        headers={["status variable", "value", "meaning"]}
        rows={[
          ["ANOMALY_MEDIATION_INPUT_STATUS", "VERIFIED", "authorization present and frozen"],
          ["CONFORMAL_COMPENSATOR_STATUS", "VERIFIED", "Phi_C TEST EXTENSION input"],
          ["GAUGINO_MASS_ANOMALY_STATUS", "PARTIAL", "M_a ~ (beta/g) F_phi; beta is REFERENCE_ONLY"],
          ["SCALAR_SOFT_MASS_ANOMALY_STATUS", "PARTIAL", "minus one over four * d gamma / d ln mu * |F_phi|^2"],
          ["A_TERM_ANOMALY_STATUS", "PARTIAL", "A_y ~ beta_y F_phi when beta_y exists"],
          ["B_TERM_ANOMALY_STATUS", "PARTIAL", "structurally dependent; not fabricated"],
          ["RG_CONSISTENCY_STATUS", "PARTIAL", "P5J/P5K not upgraded"],
          ["GAUGE_COUPLING_CONSTRAINT_STATUS", "FREE", "used, not determined"],
          ["R_SYMMETRY_STATUS", "PARTIAL", "not assumed from super-Weyl"],
          ["SUGRA_COMPATIBILITY_STATUS", "PARTIAL", "compensator extra to 11U"],
          ["VACUUM / MODULI / UV impact", "PARTIAL / NOT_FOUND / NOT_FOUND", "no selection, no completion"],
          ["PARAMETER_REDUCTION / PFR", "NONE / NOT_FOUND", "one new parameter, zero PFRs"],
        ]}
        striped
        rowTone={[
          "success",
          "success",
          "warning",
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

      <Grid columns={2} gap={16}>
        <Card>
          <CardHeader>Derived given the input</CardHeader>
          <CardBody>
            <Stack gap={8}>
              <Text>
                Gaugino map is one-loop / RG-order 1. Scalar map is two-loop /
                RG-order 2. Sign of m_i^2 stays indefinite.
              </Text>
              <Text>
                M_a / g^2 still depends on beta, F_phi, and scheme. It is not
                counted as a PFR.
              </Text>
            </Stack>
          </CardBody>
        </Card>
        <Card>
          <CardHeader>Isolation and remaining freedom</CardHeader>
          <CardBody>
            <Stack gap={8}>
              <Text>
                Gravity mediation previously tested, PARTIAL. Gauge mediation
                previously tested, PARTIAL. Documentary comparison only.
              </Text>
              <Text>
                c0, c1, lambda_a, lambda_b, xi, W, K remain free. Modulus and
                direct mediation NOT ACTIVATED. 11V and 11X hashes unchanged.
              </Text>
            </Stack>
          </CardBody>
        </Card>
      </Grid>

      <Divider />
      <Text tone="secondary">
        Hierarchy kept: beta functions ≠ anomaly mediation. F_phi ≠ F_X.
        Anomaly mediation ≠ unique mechanism ≠ vacuum selection ≠ UV completion.
        PHASE_11Y_STOPPED = TRUE. Next phase requires a separate authorization.
      </Text>
    </Stack>
  );
}
