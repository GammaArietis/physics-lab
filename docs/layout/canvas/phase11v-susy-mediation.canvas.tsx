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

export default function Phase11VSusyMediation() {
  return (
    <Stack gap={24}>
      <Stack gap={8}>
        <H1>Mediation as input</H1>
        <Text tone="secondary">
          Phase 11V transmits SUSY breaking only after a mediation mechanism is
          authorized as a new physical input. Supergravity is not gravity
          mediation. Source: phase11v-susy-mediation-v1 ·
          HUMAN-SUSY-MEDIATION-AUTHORIZATION-v1 · MINIMAL GRAVITY-MEDIATED
          TEST EXTENSION · frozen 4C c26df583… · 2026-09-25.
        </Text>
        <Row gap={8} wrap>
          <Pill active>NEW PHYSICAL INPUT</Pill>
          <Pill tone="warning" active>
            UNIQUE_MEDIATION NOT_DERIVED
          </Pill>
          <Pill active>M is INPUT</Pill>
          <Pill tone="neutral" active>
            other branches UNTESTED
          </Pill>
        </Row>
      </Stack>

      <Callout tone="warning" title="Breaking does not choose a messenger">
        Under the authorized gravity-mediation input, an abstract hidden chiral
        X with F_X nonzero communicates through M-suppressed TEST TERMS. Soft
        terms exist; their coefficients are not fixed. Gauge, anomaly, modulus,
        and direct mediation were not activated.
      </Callout>

      <Grid columns={4} gap={12}>
        <Stat value="ABSENT" label="coverage before 11V" />
        <Stat value="PARTIAL" label="gravity mediation / SUGRA fit" />
        <Stat value="1" label="new parameter (M)" />
        <Stat value="NOT_DERIVED" label="unique mediation" />
      </Grid>

      <H2>Authorized branch versus silent branches</H2>
      <Table
        headers={["mechanism", "status", "what was shown"]}
        rows={[
          ["gravity mediation", "PARTIAL", "hidden X, F_X, M-suppressed TEST TERMS"],
          ["gauge mediation", "UNTESTED", "no messengers; U(1) does not imply it"],
          ["anomaly mediation", "UNTESTED", "beta functions do not imply it"],
          ["modulus mediation", "UNTESTED", "generic moduli do not imply it"],
          ["direct mediation", "UNTESTED", "not authorized"],
        ]}
        striped
        rowTone={["warning", "neutral", "neutral", "neutral", "neutral"]}
      />

      <H2>Generated structure, unfixed coefficients</H2>
      <Table
        headers={["object", "exists?", "coefficient", "provenance"]}
        rows={[
          ["scalar soft masses", "yes", "~ |F_X|^2 / M^2, not fixed", "DERIVED GIVEN INPUT"],
          ["gaugino masses", "yes", "~ F_X / M, not fixed", "DERIVED GIVEN INPUT"],
          ["A/B-like terms", "schematic", "not uniquely fixed", "DERIVED GIVEN INPUT"],
          ["mediation scale M", "yes", "free INPUT", "INPUT"],
          ["11T m2_soft", "kept", "not promoted to SUGRA-soft", "11T INPUT"],
        ]}
        striped
      />

      <Grid columns={2} gap={16}>
        <Card>
          <CardHeader>Derived given the input</CardHeader>
          <CardBody>
            <Stack gap={8}>
              <Text>
                Dim-6 (Xbar X)(Qbar Q)/M^2 and dim-5 X W W / M are distinct
                MEDIATION TEST TERMS. A nonzero F_X does not determine M.
              </Text>
              <Text>
                SUGRA compatibility remains PARTIAL: 11U did not rewrite frozen
                c0+c1 R, and the rigid soft term is not automatically a
                supergravity soft term.
              </Text>
            </Stack>
          </CardBody>
        </Card>
        <Card>
          <CardHeader>Still free / still PARTIAL</CardHeader>
          <CardBody>
            <Stack gap={8}>
              <Text>c0, c1, lambda_a, lambda_b, gauge coupling, W, K.</Text>
              <Text>M free. Soft coefficients unfixed. No unique vacuum.</Text>
              <Text>
                Vacuum selection NOT_FOUND. UV PROPERTY NOT FOUND. Sequestering
                not inserted. New PFR count: 0.
              </Text>
            </Stack>
          </CardBody>
        </Card>
      </Grid>

      <Divider />
      <Text tone="secondary">
        Hierarchy kept: mediation mechanism ≠ scale determination. Soft-term
        generation ≠ numerical prediction. Mediation ≠ vacuum selection ≠ UV
        completion. No strings, GUT, or experimental superpartner masses.
      </Text>
    </Stack>
  );
}
