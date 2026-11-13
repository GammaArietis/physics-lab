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

export default function Phase11XGaugeMediation() {
  return (
    <Stack gap={24}>
      <Stack gap={8}>
        <H1>Gauge mediation as input</H1>
        <Text tone="secondary">
          Phase 11X activates only gauge mediation as a new physical input. It
          is a separate TEST EXTENSION from 11V gravity mediation, not a
          preferred mechanism. Source: phase11x-gauge-mediation-v1 ·
          HUMAN-SUSY-MEDIATION-GAUGE-AUTHORIZATION-v1 · existing U(1)
          vector-like messengers · frozen 4C c26df583… · 2026-09-25.
        </Text>
        <Row gap={8} wrap>
          <Pill active>NEW PHYSICAL INPUT</Pill>
          <Pill tone="warning" active>
            UNIQUENESS NOT_DERIVED
          </Pill>
          <Pill active>y and M independent</Pill>
          <Pill tone="neutral" active>
            11V isolated
          </Pill>
        </Row>
      </Stack>

      <Callout tone="warning" title="U(1) is not a messenger sector">
        Under the authorized gauge-mediation input, a hidden chiral X with F_X
        nonzero communicates through a vector-like messenger pair and existing
        gauge loops. Soft terms exist at one and two loops; their coefficients
        are not fixed. Anomaly cancellation does not select a unique charge or
        multiplicity.
      </Callout>

      <Grid columns={4} gap={12}>
        <Stat value="ABSENT" label="coverage before 11X" />
        <Stat value="VERIFIED" label="W_mess / vector-like anomaly" />
        <Stat value="2" label="new parameters (M, y)" />
        <Stat value="NOT_DERIVED" label="unique messenger sector" />
      </Grid>

      <H2>Generated structure, unfixed coefficients</H2>
      <Table
        headers={["object", "generated?", "order / status", "coefficient"]}
        rows={[
          ["W_mess = y X Psi barPsi + M Psi barPsi", "yes", "INPUT", "y, M free"],
          ["gaugino masses", "yes", "one loop", "PARAMETER-DEPENDENT"],
          ["scalar soft masses", "yes", "two loop", "PARAMETER-DEPENDENT"],
          ["A/B terms", "not automatic", "PARTIAL", "not manufactured"],
          ["messenger representation", "vector-like U(1)", "PARTIAL", "q, multiplicity free"],
        ]}
        striped
        rowTone={["success", "success", "success", "warning", "warning"]}
      />

      <Grid columns={2} gap={16}>
        <Card>
          <CardHeader>Derived given the input</CardHeader>
          <CardBody>
            <Stack gap={8}>
              <Text>
                A vector-like partner is required by gauge-mediation
                consistency so the cubic U(1) anomaly cancels. A single charged
                Weyl messenger is not used.
              </Text>
              <Text>
                Schematic gaugino mass depends on g, y, F_X, and M. F_X does
                not determine M. y is not collapsed into M.
              </Text>
            </Stack>
          </CardBody>
        </Card>
        <Card>
          <CardHeader>Still free / still PARTIAL</CardHeader>
          <CardBody>
            <Stack gap={8}>
              <Text>c0, c1, lambda_a, lambda_b, gauge coupling, xi, W, K.</Text>
              <Text>
                Messenger charge and multiplicity not unique. Gravity mediation
                unchanged. MEDIATION_SELECTION remains NOT_DERIVED.
              </Text>
              <Text>
                SUGRA embedding of messengers PARTIAL. UV PROPERTY NOT FOUND.
                Vacuum selection NOT_FOUND. New PFR count: 0.
              </Text>
            </Stack>
          </CardBody>
        </Card>
      </Grid>

      <Divider />
      <Text tone="secondary">
        Hierarchy kept: messenger content ≠ scale determination. Soft-term
        generation ≠ numerical prediction. Gauge mediation ≠ unique mediation
        mechanism ≠ vacuum selection ≠ UV completion. No ranking versus 11V.
      </Text>
    </Stack>
  );
}
