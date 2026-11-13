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

export default function Phase11QUVConsistency() {
  return (
    <Stack gap={24}>
      <Stack gap={8}>
        <H1>UV consistency</H1>
        <Text tone="secondary">
          Phase 11Q audits whether the existing project forces a UV
          completion. It does not. UV property not found is not UV
          inconsistency. Source: phase11q-uv-consistency-v1 · frozen 4C
          c26df583… · 2026-09-25.
        </Text>
        <Row gap={8} wrap>
          <Pill active>AUDIT ONLY</Pill>
          <Pill tone="warning" active>
            UV PROPERTY NOT FOUND
          </Pill>
          <Pill active>not UV inconsistency</Pill>
          <Pill active>P5K Gamma masters, not Meijer</Pill>
        </Row>
      </Stack>

      <Callout tone="warning" title="A beta function is not a UV completion">
        One- and two-loop gauge RG exist in TEST EXTENSION scope. A beta
        function does not fix its boundary value. Candidate-dependent
        asymptotic freedom does not select a unique theory.
      </Callout>

      <Grid columns={4} gap={12}>
        <Stat value="PARTIAL" label="coverage before" />
        <Stat value="PARTIAL" label="coverage after" />
        <Stat value="UNTESTED" label="nonperturbative UV" />
        <Stat value="UNTESTED" label="quantum gravity UV" />
      </Grid>

      <H2>UV hierarchy</H2>
      <Table
        headers={["level", "status", "note"]}
        rows={[
          ["perturbative calculation", "PARTIAL", "P5G one-loop, P5K two-loop"],
          ["renormalization", "PARTIAL", "Q07 in P5G one-loop scope"],
          ["renormalizability", "PARTIAL", "mixed: scalar dim-four vs gravity"],
          ["asymptotic freedom", "PARTIAL", "Q09 TESTED_PER_CANDIDATE"],
          ["fixed point", "PARTIAL", "truncated; not a physical prediction"],
          ["asymptotic safety", "UNTESTED", "not assumed"],
          ["nonperturbative completion", "UNTESTED", "UV PROPERTY NOT FOUND"],
        ]}
        striped
        rowTone={[
          "warning",
          "warning",
          "warning",
          "warning",
          "warning",
          "neutral",
          "neutral",
        ]}
      />

      <H2>Coverage matrix</H2>
      <Table
        headers={["ingredient", "scalar", "gauge", "Weyl", "mixed", "gravity", "status"]}
        rows={[
          ["power counting", "PARTIAL", "PARTIAL", "PARTIAL", "PARTIAL", "PARTIAL", "PARTIAL"],
          ["beta functions", "UNTESTED", "PARTIAL", "PARTIAL", "PARTIAL", "UNTESTED", "PARTIAL"],
          ["asymptotic freedom", "UNTESTED", "PARTIAL", "PARTIAL", "PARTIAL", "UNTESTED", "PARTIAL"],
          ["Landau-pole behavior", "UNTESTED", "UNTESTED", "UNTESTED", "UNTESTED", "UNTESTED", "UNTESTED"],
          ["fixed points", "UNTESTED", "PARTIAL", "UNTESTED", "UNTESTED", "UNTESTED", "PARTIAL"],
          ["UV closure", "PARTIAL", "PARTIAL", "PARTIAL", "PARTIAL", "UNTESTED", "PARTIAL"],
          ["nonperturbative completion", "UNTESTED", "UNTESTED", "UNTESTED", "UNTESTED", "UNTESTED", "UNTESTED"],
        ]}
        striped
        stickyHeader
        rowTone={[
          "warning",
          "warning",
          "neutral",
          "warning",
          "warning",
          "neutral",
        ]}
      />

      <Grid columns={2} gap={16}>
        <Card>
          <CardHeader>Verified UV facts</CardHeader>
          <CardBody>
            <Stack gap={8}>
              <Text>
                Frozen gravity remains ∫ √(-g)(c0 + c1 R). Higher-curvature
                operators were not added.
              </Text>
              <Text>
                P5J did not recompute betas. P5K did not hardcode textbook
                betas. Production method: Beta/Gamma master integrals.
              </Text>
              <Text>c0, c1, lambda_a, lambda_b remain free. Vacuum selection stays NOT_FOUND.</Text>
            </Stack>
          </CardBody>
        </Card>
        <Card>
          <CardHeader>Left open</CardHeader>
          <CardBody>
            <Stack gap={8}>
              <Text>Nonperturbative UV completion and physical Landau pole.</Text>
              <Text>Gravity beta functions and asymptotic safety.</Text>
              <Text>Wilsonian matching; a cutoff value was not introduced.</Text>
              <Text>
                Unique gauge group or vacuum from UV friendliness. That would
                need a new physical-input module.
              </Text>
            </Stack>
          </CardBody>
        </Card>
      </Grid>

      <Divider />
      <Text tone="secondary">
        Hierarchy kept: perturbative calculation ≠ renormalization ≠
        renormalizability ≠ asymptotic freedom ≠ fixed point ≠ asymptotic
        safety ≠ nonperturbative UV completion. M6–M10, global gauge,
        gravity–matter, and vacuum stay PARTIAL. New parameters: 0.
      </Text>
    </Stack>
  );
}
