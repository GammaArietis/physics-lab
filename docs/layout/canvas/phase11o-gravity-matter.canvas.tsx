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

export default function Phase11OGravityMatter() {
  return (
    <Stack gap={24}>
      <Stack gap={8}>
        <H1>Gravity–matter consistency</H1>
        <Text tone="secondary">
          Phase 11O audits the existing gravity–matter interface. Covariance
          plus conservation do not fix c0, c1, and do not select unique
          minimal coupling. Source: phase11o-gravity-matter-v1 · frozen 4C
          c26df583… · 2026-09-25.
        </Text>
        <Row gap={8} wrap>
          <Pill active>AUDIT ONLY</Pill>
          <Pill tone="warning" active>
            minimal coupling NOT_UNIQUE
          </Pill>
          <Pill active>c0, c1 FREE</Pill>
          <Pill active>M6–M10 and 11N stay PARTIAL</Pill>
        </Row>
      </Stack>

      <Callout tone="warning" title="General covariance is not an equivalence principle">
        The frozen action is built from scalar densities. That is structural
        metric coupling of the existing construction. It is not a derived
        equivalence principle, a unique minimal-coupling theorem, or a
        gravitational scale.
      </Callout>

      <Grid columns={4} gap={12}>
        <Stat value="PARTIAL" label="coverage before" />
        <Stat value="PARTIAL" label="coverage after" />
        <Stat value="NOT UNIQUE" label="minimal coupling" tone="warning" />
        <Stat value="UNTESTED" label="quantum gravity" />
      </Grid>

      <H2>Coverage matrix</H2>
      <Table
        headers={[
          "ingredient",
          "scalar",
          "internal",
          "U(1)",
          "F² test",
          "Weyl",
          "status",
        ]}
        rows={[
          ["diffeomorphism covariance", "VERIFIED", "VERIFIED", "PARTIAL", "PARTIAL", "UNTESTED", "PARTIAL"],
          ["stress-energy tensor", "PARTIAL", "PARTIAL", "ABSENT in 5C", "PARTIAL", "UNTESTED", "PARTIAL"],
          ["Bianchi compatibility", "PARTIAL", "PARTIAL", "PARTIAL", "PARTIAL", "UNTESTED", "PARTIAL"],
          ["matter conservation", "PARTIAL", "PARTIAL", "PARTIAL", "PARTIAL", "UNTESTED", "PARTIAL"],
          ["gauge-current conservation", "PARTIAL", "PARTIAL", "PARTIAL", "PARTIAL", "UNTESTED", "PARTIAL"],
          ["gauge–gravity compatibility", "PARTIAL", "PARTIAL", "PARTIAL", "PARTIAL", "UNTESTED", "PARTIAL"],
          ["backreaction", "UNTESTED", "UNTESTED", "UNTESTED", "UNTESTED", "UNTESTED", "UNTESTED"],
          ["minimal coupling", "NOT_UNIQUE", "NOT_UNIQUE", "NOT_UNIQUE", "ASSUMED", "UNTESTED", "NOT_UNIQUE"],
          ["nonminimal curvature", "NOT_SELECTED", "NOT_SELECTED", "NOT_SELECTED", "NOT_SELECTED", "UNTESTED", "UNTESTED"],
          ["equivalence principle", "UNTESTED", "UNTESTED", "UNTESTED", "UNTESTED", "UNTESTED", "UNTESTED"],
          ["gravitational normalization", "UNTESTED", "UNTESTED", "UNTESTED", "UNTESTED", "UNTESTED", "UNTESTED"],
          ["quantum gravity", "UNTESTED", "UNTESTED", "UNTESTED", "UNTESTED", "UNTESTED", "UNTESTED"],
        ]}
        striped
        stickyHeader
        rowTone={[
          "warning",
          "warning",
          "warning",
          "warning",
          "warning",
          "warning",
          "neutral",
          "warning",
          "neutral",
          "neutral",
          "neutral",
          "neutral",
        ]}
      />

      <H2>Parameter report</H2>
      <Table
        headers={["quantity", "status", "provenance", "constrained by gravity–matter?"]}
        rows={[
          ["c0", "FREE", "INPUT", "no"],
          ["c1", "FREE", "INPUT", "no"],
          ["Z", "FREE", "INPUT", "no"],
          ["lambda_a", "FREE", "INPUT / H_int", "no"],
          ["lambda_b", "FREE", "INPUT / H_int", "no"],
          ["gauge normalization", "FREE in 5D TEST COPY", "TEST EXTENSION", "no"],
          ["g", "not derived", "UNTESTED", "no"],
          ["Z_A", "FREE in 5D TEST COPY", "TEST EXTENSION", "no"],
        ]}
        striped
      />

      <Grid columns={2} gap={16}>
        <Card>
          <CardHeader>Verified existing results</CardHeader>
          <CardBody>
            <Stack gap={8}>
              <Text>
                Gravity family remains ∫ √(-g)(c0 + c1 R) with both coefficients
                free.
              </Text>
              <Text>
                Frozen kinetic term uses the inverse metric. Internal SO(2) is
                independent of diffeomorphisms.
              </Text>
              <Text>
                H_int commutes with K. The ratio lambda_a / lambda_b is not a
                number. No new gravity–matter parameter-free relation.
              </Text>
            </Stack>
          </CardBody>
        </Card>
        <Card>
          <CardHeader>Left open</CardHeader>
          <CardBody>
            <Stack gap={8}>
              <Text>Solved backreaction, existence, stability, uniqueness.</Text>
              <Text>Minimal-coupling uniqueness and R Φ² exclusion.</Text>
              <Text>Equivalence principle as a theorem; trajectory universality.</Text>
              <Text>Gravitational scale and quantum gravity.</Text>
            </Stack>
          </CardBody>
        </Card>
      </Grid>

      <Divider />
      <Text tone="secondary">
        Hierarchy kept: covariance ≠ stress-energy ≠ Bianchi ≠ matter
        conservation ≠ gauge current ≠ gauge–gravity compatibility ≠ unique
        minimal coupling ≠ equivalence principle ≠ gravitational
        normalization ≠ quantum gravity. New parameters: 0. New
        parameter-free relations: 0.
      </Text>
    </Stack>
  );
}
