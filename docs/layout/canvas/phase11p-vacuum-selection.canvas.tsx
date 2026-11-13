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

export default function Phase11PVacuumSelection() {
  return (
    <Stack gap={24}>
      <Stack gap={8}>
        <H1>Vacuum selection</H1>
        <Text tone="secondary">
          Phase 11P audits whether the existing theory contains an intrinsic
          principle that selects a unique vacuum. It does not. Source:
          phase11p-vacuum-selection-v1 · frozen 4C c26df583… · 2026-09-25.
        </Text>
        <Row gap={8} wrap>
          <Pill active>AUDIT ONLY</Pill>
          <Pill tone="warning" active>
            selection principle NOT_FOUND
          </Pill>
          <Pill active>uniqueness NOT_DERIVED</Pill>
          <Pill active>moduli remain</Pill>
        </Row>
      </Stack>

      <Callout tone="warning" title="Stationarity is not vacuum selection">
        Phi = 0 is always stationary for the implemented quadratic. Local
        stability depends on the sign of mu_s_sq. That is existence plus
        parameter-dependent stability. It is not a unique vacuum of the
        theory.
      </Callout>

      <Grid columns={4} gap={12}>
        <Stat value="PARTIAL" label="coverage before" />
        <Stat value="PARTIAL" label="coverage after" />
        <Stat value="NOT FOUND" label="selection principle" tone="warning" />
        <Stat value="NOT DERIVED" label="uniqueness" tone="warning" />
      </Grid>

      <H2>Hierarchy</H2>
      <Table
        headers={["level", "status", "note"]}
        rows={[
          ["stationary point", "PARTIAL", "Phi=0 always; all constant Phi if mu_s_sq=0"],
          ["local minimum", "PARTIAL", "Hessian = 2 mu_s_sq identity"],
          ["global minimum", "UNTESTED", "positive Hessian is not a general global min"],
          ["physical state", "UNTESTED", "BRST does not construct a vacuum vector"],
          ["vacuum", "PARTIAL", "candidate Q0 exists; not selected"],
          ["selected vacuum", "NOT_FOUND", "no existing principle selects one state"],
          ["unique vacuum", "NOT_DERIVED", "moduli remain; M3 stays PARTIAL"],
        ]}
        striped
        rowTone={[
          "warning",
          "warning",
          "neutral",
          "neutral",
          "warning",
          "warning",
          "warning",
        ]}
      />

      <H2>Coverage matrix</H2>
      <Table
        headers={["ingredient", "scalar", "internal", "U(1)", "gravity–matter", "quantum", "status"]}
        rows={[
          ["stationary points", "PARTIAL", "PARTIAL", "PARTIAL", "UNTESTED", "UNTESTED", "PARTIAL"],
          ["local stability", "PARTIAL", "PARTIAL", "UNTESTED", "UNTESTED", "UNTESTED", "PARTIAL"],
          ["global minimum", "UNTESTED", "UNTESTED", "UNTESTED", "UNTESTED", "UNTESTED", "UNTESTED"],
          ["moduli", "VERIFIED", "VERIFIED", "PARTIAL", "UNTESTED", "UNTESTED", "VERIFIED"],
          ["vacuum selection", "NOT_FOUND", "NOT_FOUND", "NOT_FOUND", "NOT_FOUND", "NOT_FOUND", "NOT_FOUND"],
          ["vacuum uniqueness", "NOT_DERIVED", "NOT_DERIVED", "NOT_DERIVED", "NOT_DERIVED", "NOT_DERIVED", "NOT_DERIVED"],
          ["interacting vacuum", "UNTESTED", "UNTESTED", "UNTESTED", "UNTESTED", "UNTESTED", "UNTESTED"],
          ["gravity-induced selection", "UNTESTED", "UNTESTED", "UNTESTED", "UNTESTED", "UNTESTED", "UNTESTED"],
        ]}
        striped
        stickyHeader
        rowTone={[
          "warning",
          "warning",
          "neutral",
          "success",
          "warning",
          "warning",
          "neutral",
          "neutral",
        ]}
      />

      <Grid columns={2} gap={16}>
        <Card>
          <CardHeader>What is certified</CardHeader>
          <CardBody>
            <Stack gap={8}>
              <Text>
                Phi = 0 is stationary. SO(2) leaves V invariant. H_int two-plane
                degeneracy is spectral, not a vacuum statement.
              </Text>
              <Text>
                Gauge copies of A = 0 are not new physical vacua. Global-symmetry
                copies are not quotiented without justification.
              </Text>
              <Text>c0 and c1 remain free. No new parameter-free relation.</Text>
            </Stack>
          </CardBody>
        </Card>
        <Card>
          <CardHeader>Left open</CardHeader>
          <CardBody>
            <Stack gap={8}>
              <Text>Global minimum of a general potential.</Text>
              <Text>Interacting quantum vacuum and BRST vacuum vector.</Text>
              <Text>Gravity-induced selection; solved backreaction.</Text>
              <Text>
                Any uniqueness theorem. That would need a new selection
                principle, a justified symmetry quotient, or a new boundary
                condition.
              </Text>
            </Stack>
          </CardBody>
        </Card>
      </Grid>

      <Divider />
      <Text tone="secondary">
        Hierarchy kept: stationary point ≠ local minimum ≠ global minimum ≠
        physical state ≠ vacuum ≠ selected vacuum ≠ unique vacuum. M3, M6–M10,
        global gauge, and gravity–matter stay PARTIAL. New parameters: 0.
      </Text>
    </Stack>
  );
}
