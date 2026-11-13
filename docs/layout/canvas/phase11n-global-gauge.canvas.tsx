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

export default function Phase11NGlobalGauge() {
  return (
    <Stack gap={24}>
      <Stack gap={8}>
        <H1>Global gauge structure</H1>
        <Text tone="secondary">
          Phase 11N audits which layers of gauge structure are already
          certified. Local U(1) plus compactness do not fix a unique global
          form. Source: phase11n-global-gauge-v1 · frozen 4C c26df583… ·
          2026-09-25.
        </Text>
        <Row gap={8} wrap>
          <Pill active>AUDIT ONLY</Pill>
          <Pill tone="warning" active>
            global form NOT_UNIQUE
          </Pill>
          <Pill active>M6–M10 stay PARTIAL</Pill>
          <Pill active>coupling remains free</Pill>
        </Row>
      </Stack>

      <Callout tone="warning" title="Local gauging is not a global group theorem">
        Phase 5C established a local U(1) connection on a contractible patch.
        That does not select a covering class, a quotient, a bundle, or a
        physical coupling. Those layers stay open.
      </Callout>

      <Grid columns={4} gap={12}>
        <Stat value="PARTIAL" label="coverage before" />
        <Stat value="PARTIAL" label="coverage after" />
        <Stat value="NOT UNIQUE" label="global group form" tone="warning" />
        <Stat value="UNTESTED" label="bundles / large gauge" />
      </Grid>

      <H2>Coverage matrix</H2>
      <Table
        headers={["ingredient", "U(1)", "non-Abelian", "product groups", "status"]}
        rows={[
          ["local gauge symmetry", "VERIFIED", "PARTIAL", "PARTIAL", "PARTIAL"],
          ["compactness", "VERIFIED", "PARTIAL", "PARTIAL", "PARTIAL"],
          ["global group form", "PARTIAL", "UNTESTED", "UNTESTED", "PARTIAL"],
          ["representation kernel", "VERIFIED", "UNTESTED", "UNTESTED", "PARTIAL"],
          ["faithfulness", "VERIFIED", "UNTESTED", "UNTESTED", "PARTIAL"],
          ["weight / charge lattice", "PARTIAL", "PARTIAL", "PARTIAL", "PARTIAL"],
          ["center action", "PARTIAL", "UNTESTED", "UNTESTED", "UNTESTED"],
          ["quotient structure", "UNTESTED", "UNTESTED", "UNTESTED", "UNTESTED"],
          ["large gauge transformations", "UNTESTED", "UNTESTED", "UNTESTED", "UNTESTED"],
          ["bundle topology", "UNTESTED", "UNTESTED", "UNTESTED", "UNTESTED"],
          ["anomaly constraints", "PARTIAL", "PARTIAL", "PARTIAL", "PARTIAL"],
          ["global uniqueness", "NOT_UNIQUE", "NOT DERIVED", "NOT DERIVED", "PARTIAL"],
        ]}
        striped
        stickyHeader
        rowTone={[
          "success",
          "success",
          "warning",
          "warning",
          "warning",
          "warning",
          "neutral",
          "neutral",
          "neutral",
          "neutral",
          "warning",
          "warning",
        ]}
      />

      <Grid columns={2} gap={16}>
        <Card>
          <CardHeader>Verified existing structure</CardHeader>
          <CardBody>
            <Stack gap={8}>
              <Text>Exact global SO(2) congruent to U(1) from Phase 5B.0.</Text>
              <Text>Local U(1) gauging possible as a Phase 5C test copy.</Text>
              <Text>
                Stored real representation: U(α + 2π) = U(α), kernel α ∈ 2πℤ,
                faithful as SO(2) on the 2-plane.
              </Text>
              <Text>G5/G6 do not select a unique gauge theory. g and Z_A stay free.</Text>
            </Stack>
          </CardBody>
        </Card>
        <Card>
          <CardHeader>Left open</CardHeader>
          <CardBody>
            <Stack gap={8}>
              <Text>Covering class and global form uniqueness.</Text>
              <Text>Quotient identifications and center-implied quotients.</Text>
              <Text>Nontrivial bundles, large gauge transformations, line operators.</Text>
              <Text>
                Absolute charge units and physical coupling. Compactness is not
                a generator-normalization theorem.
              </Text>
            </Stack>
          </CardBody>
        </Card>
      </Grid>

      <Divider />
      <Text tone="secondary">
        Hierarchy kept: local gauge ≠ compactness ≠ representation lattice ≠
        faithful image ≠ global form ≠ bundle topology ≠ dynamics ≠ coupling.
        New parameters: 0. New parameter-free relations: 0.
      </Text>
    </Stack>
  );
}
