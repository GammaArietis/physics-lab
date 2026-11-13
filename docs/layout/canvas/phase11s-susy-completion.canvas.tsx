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

export default function Phase11SSusyCompletion() {
  return (
    <Stack gap={24}>
      <Stack gap={8}>
        <H1>Rigid N=1 completion</H1>
        <Text tone="secondary">
          Phase 11S extracts further consequences of HUMAN-SUSY-AUTHORIZATION-v1.
          It does not add a second input. Source: phase11s-susy-completion-v1 ·
          frozen 4C c26df583… · 2026-09-25.
        </Text>
        <Row gap={8} wrap>
          <Pill active>same authorization</Pill>
          <Pill tone="success" active>
            off-shell TEST EXTENSION
          </Pill>
          <Pill tone="warning" active>
            W not unique
          </Pill>
          <Pill active>PFR count 0</Pill>
        </Row>
      </Stack>

      <Callout tone="warning" title="Completion is not uniqueness">
        Under the already authorized rigid N=1 input, chiral and vector
        TEST EXTENSIONS now close off-shell with F and D. The superpotential
        remains a free holomorphic function. Unique theory is not derived.
      </Callout>

      <Grid columns={4} gap={12}>
        <Stat value="VERIFIED" label="chiral / vector / closure" />
        <Stat value="PARTIAL" label="module after" />
        <Stat value="0" label="new PFR after audit" />
        <Stat value="NOT_DERIVED" label="unique W / unique theory" />
      </Grid>

      <H2>Implementation gap versus undetermined physics</H2>
      <Table
        headers={["item", "11R", "11S", "kind"]}
        rows={[
          ["explicit transformations", "schematic", "VERIFIED", "implementation gap closed"],
          ["off-shell commutator", "not executed", "VERIFIED in TEST EXTENSION", "implementation gap closed"],
          ["invariant free action", "missing", "VERIFIED", "implementation gap closed"],
          ["F elimination / V_F", "named", "VERIFIED: |W_phi|^2", "implementation gap closed"],
          ["unique W", "not derived", "still not derived", "physical result not determined"],
          ["unique vacuum", "not derived", "still not derived", "physical result not determined"],
          ["cubic numerical ratio", "counted as PFR", "convention-dependent; not a PFR", "convention audit"],
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
        ]}
      />

      <H2>Forced given W, still free overall</H2>
      <Table
        headers={["relation", "forced by SUSY?", "independent of W parametrization?"]}
        rows={[
          ["F = −∂W/∂phi (sign = CONVENTION)", "yes, given W", "sign is convention; V_F is not"],
          ["V_F = |W_phi|^2", "yes, given W", "yes"],
          ["Yukawa from W_phiphi", "yes, given W", "absolute factor is CONVENTION"],
          ["common symbolic g on scalar, fermion, gaugino vertices", "yes", "g0 itself remains free"],
          ["holomorphic W", "no — still a free function", "SUPERPOTENTIAL_UNIQUENESS NOT_DERIVED"],
        ]}
        striped
      />

      <Grid columns={2} gap={16}>
        <Card>
          <CardHeader>Closed in the TEST EXTENSION</CardHeader>
          <CardBody>
            <Stack gap={8}>
              <Text>
                Complex phi is a representational requirement. Real Phi is not
                a chiral multiplet. A_mu is not a vector multiplet without
                lambda and D.
              </Text>
              <Text>
                [δ1, δ2] on phi is a translation; the F remainder cancels.
                On A_mu it is a translation plus a U(1) gauge transformation.
              </Text>
            </Stack>
          </CardBody>
        </Card>
        <Card>
          <CardHeader>Still open</CardHeader>
          <CardBody>
            <Stack gap={8}>
              <Text>Unique vacuum, unique gauge form, c0, c1, lambda_a, lambda_b.</Text>
              <Text>Anomaly cancellation as a model selector.</Text>
              <Text>UV completion; 11Q stays PARTIAL.</Text>
              <Text>Supergravity remains required only for a stronger gravity claim and was not added.</Text>
            </Stack>
          </CardBody>
        </Card>
      </Grid>

      <Divider />
      <Text tone="secondary">
        Reduced parameter count 2 and optional xi (count 1) revalidated.
        Remaining free function: holomorphic W. M6–M10, global gauge,
        vacuum selection, and UV stay PARTIAL.
      </Text>
    </Stack>
  );
}
