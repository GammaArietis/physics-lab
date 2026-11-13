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

export default function Phase11AE1Containment() {
  return (
    <Stack gap={24}>
      <Stack gap={8}>
        <H1>Global-minimum selection is not contained</H1>
        <Text tone="secondary">
          Phase 11AE.1 asks whether a ground-state / global-minimum criterion
          is already inside the laboratory. It is not. Source:
          phase11ae1-containment-v1 · frozen 4C c26df583… · 2026-09-25.
        </Text>
        <Row gap={8} wrap>
          <Pill tone="warning" active>
            REQUIRES_NEW_ASSUMPTION
          </Pill>
          <Pill tone="deleted" active>
            NOT_CONTAINED
          </Pill>
          <Pill tone="neutral" active>
            PHASE_11AE1_STOPPED
          </Pill>
        </Row>
      </Stack>

      <Callout tone="warning" title="Containment audit only">
        No vacuum-selection law was activated. External phrases such as vacuum
        equals lowest energy remain REFERENCE_ONLY. Stationarity is not
        selection. Local stability is not a global minimum.
      </Callout>

      <Grid columns={4} gap={12}>
        <Stat value="PARTIAL" label="energy functional" />
        <Stat value="ABSENT" label="global minimization" />
        <Stat value="NOT_ESTABLISHED" label="local vs global" />
        <Stat value="NOT_FOUND" label="modulus stabilization" />
      </Grid>

      <H2>A–G ingredients of vacuum in argmin Functional</H2>
      <Table
        headers={["ingredient", "status", "assumption needed?"]}
        rows={[
          ["A. the functional", "PARTIAL", "yes"],
          ["B. admissible configuration space", "PARTIAL", "yes"],
          ["C. relevant constraints", "ABSENT", "yes"],
          ["D. global optimization relation", "ABSENT", "yes"],
          ["E. existence of a minimum", "NOT_ESTABLISHED", "yes"],
          ["F. global vs local", "NOT_ESTABLISHED", "no extra law"],
          ["G. minimum is the physical vacuum", "ABSENT", "yes"],
        ]}
        striped
        rowTone={[
          "warning",
          "warning",
          "danger",
          "danger",
          "warning",
          "warning",
          "danger",
        ]}
      />

      <Grid columns={2} gap={16}>
        <Card>
          <CardHeader>What is already implemented</CardHeader>
          <CardBody>
            <Stack gap={8}>
              <Text>
                11P contains stationarity and Hessian cases of a quadratic
                potential, plus unlifted moduli. 11T contains F-term and D-term
                toy potentials that are not unique. 11U contains a schematic
                V_sugra identity and unclassified vacuum families.
              </Text>
              <Text>
                11Z contains T and F_T as INPUT. That is not V(T), not global
                minimization over T, and not stabilization.
              </Text>
            </Stack>
          </CardBody>
        </Card>
        <Card>
          <CardHeader>First missing ingredient</CardHeader>
          <CardBody>
            <Stack gap={8}>
              <Text>
                A complete vacuum/energy functional on a declared admissible
                space, together with the identification of its global
                minimizer with the physical vacuum.
              </Text>
              <Text>
                The blocking item is a new assumption. Global argmin machinery
                is also unimplemented. This audit does not add either.
              </Text>
            </Stack>
          </CardBody>
        </Card>
      </Grid>

      <H2>Decision</H2>
      <Table
        headers={["question", "result"]}
        rows={[
          ["Already contained?", "No"],
          ["Derivable without new assumptions?", "No"],
          ["Merely unimplemented?", "Local tools exist; the criterion is not just a missing calculation"],
          ["Requires a new assumption?", "Yes"],
          ["Selects a vacuum already?", "No"],
          ["Stabilizes moduli already?", "No"],
        ]}
        striped
      />

      <Callout tone="neutral" title="No activation">
        Even a complete global-minimization capability would not authorize
        VACUUM_SELECTION_PRINCIPLE. T09 remains REQUIRES_NEW_PHYSICAL_INPUT.
        11AE remains PRINCIPLE_UNSPECIFIED.
      </Callout>

      <Divider />
      <Text tone="secondary">
        Parents 11P, 11T, 11U, 11Z, 11AE unchanged. Frozen 4C unchanged. No
        experimental input. NEW_PARAMETER_COUNT = 0. PFR_STATUS = NOT_FOUND.
        PHASE_11AE1_STOPPED = TRUE.
      </Text>
    </Stack>
  );
}
