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

export default function Phase11ZModulusMediation() {
  return (
    <Stack gap={24}>
      <Stack gap={8}>
        <H1>Modulus mediation as input</H1>
        <Text tone="secondary">
          Phase 11Z activates only modulus mediation as a new physical input.
          Existing moduli do not derive it. Source: phase11z-modulus-mediation-v1
          · HUMAN-SUSY-MEDIATION-MODULUS-AUTHORIZATION-v1 · T and F_T INPUT ·
          f_a(T) INPUT · frozen 4C c26df583… · 2026-09-25.
        </Text>
        <Row gap={8} wrap>
          <Pill active>NEW PHYSICAL INPUT</Pill>
          <Pill tone="warning" active>
            UNIQUENESS NOT_DERIVED
          </Pill>
          <Pill active>F_T ≠ F_X, F_phi</Pill>
          <Pill tone="neutral" active>
            PHASE_11Z_STOPPED
          </Pill>
        </Row>
      </Stack>

      <Callout tone="warning" title="A modulus is not a mediation channel">
        T is a new chiral test field, not an inherited 4C–11Y modulus. F_T is
        INPUT and is not identified with F_X, F_phi, or gravitino mass. Soft
        terms use declared f_a(T) and Z_i(T, Tbar) derivatives. Gauge coupling
        remains FREE. No messengers, no mixed mediation, no direct mediation.
      </Callout>

      <Grid columns={4} gap={12}>
        <Stat value="ABSENT" label="coverage before 11Z" />
        <Stat value="2" label="new parameters (F_T, T)" />
        <Stat value="FREE" label="gauge coupling constraint" />
        <Stat value="NOT_FOUND" label="modulus stabilization" />
      </Grid>

      <H2>Required status audit</H2>
      <Table
        headers={["status variable", "value", "meaning"]}
        rows={[
          ["MODULUS_MEDIATION_INPUT_STATUS", "VERIFIED", "authorization present and frozen"],
          ["MODULUS_FIELD_STATUS", "VERIFIED", "new T; not inherited"],
          ["MODULUS_F_TERM_STATUS", "VERIFIED", "F_T INPUT"],
          ["GAUGE_KINETIC_FUNCTION_STATUS", "VERIFIED", "f_a(T) INPUT; not unique"],
          ["MODULUS_GAUGINO_MASS_STATUS", "PARTIAL", "M_a ~ F_T d ln(Re f_a)/dT"],
          ["MODULUS_SCALAR_SOFT_MASS_STATUS", "PARTIAL", "from Z_i derivatives; weights unfixed"],
          ["MODULUS_A_TERM_STATUS", "PARTIAL", "from d ln y and d ln Z when present"],
          ["MODULUS_B_TERM_STATUS", "UNTESTED", "no added bilinear structure"],
          ["MODULUS_STABILIZATION_STATUS", "NOT_FOUND", "no vacuum or mass selected"],
          ["GAUGE_COUPLING_CONSTRAINT_STATUS", "FREE", "used, not determined"],
          ["SUGRA / vacuum / UV", "PARTIAL / PARTIAL / NOT_FOUND", "no completion, no unique vacuum"],
          ["PARAMETER_REDUCTION / PFR", "NONE / NOT_FOUND", "two new parameters, zero PFRs"],
        ]}
        striped
        rowTone={[
          "success",
          "success",
          "success",
          "success",
          "warning",
          "warning",
          "warning",
          "neutral",
          "neutral",
          "success",
          "warning",
          "neutral",
        ]}
      />

      <Grid columns={2} gap={16}>
        <Card>
          <CardHeader>Derived given the input</CardHeader>
          <CardBody>
            <Stack gap={8}>
              <Text>
                Gaugino map is tree-level in the modulus derivative of Re f_a.
                Scalar and A maps use Z_i and y(T) only when those data are
                declared.
              </Text>
              <Text>
                M_a still depends on F_T and f_a(T). It is not counted as a PFR.
                Modular weights remain unfixed.
              </Text>
            </Stack>
          </CardBody>
        </Card>
        <Card>
          <CardHeader>Isolation and remaining freedom</CardHeader>
          <CardBody>
            <Stack gap={8}>
              <Text>
                Gravity, gauge, and anomaly mediation previously tested,
                PARTIAL. Documentary comparison only. No mixed mediation.
              </Text>
              <Text>
                c0, c1, lambda_a, lambda_b, xi, W, K remain free. Direct
                mediation NOT ACTIVATED. 11V, 11X, and 11Y hashes unchanged.
              </Text>
            </Stack>
          </CardBody>
        </Card>
      </Grid>

      <Divider />
      <Text tone="secondary">
        Hierarchy kept: existing moduli ≠ modulus mediation. F_T ≠ F_X ≠ F_phi.
        Modulus mediation ≠ unique mechanism ≠ stabilization ≠ UV completion.
        PHASE_11Z_STOPPED = TRUE. Next phase requires a separate authorization.
      </Text>
    </Stack>
  );
}
