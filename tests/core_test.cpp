// Offline checks of the Hall Of Meat bail tracker with synthetic skeleton motion.
#include "Extension/Skate3HallOfMeat/hom_core.h"
#include <cstdio>
#include <cmath>
#include <cmath>
#include <functional>
#include <algorithm>

using namespace dingosdk::skate3_hom;

struct Sim {
    Tracker t;
    double time = 0;
    Sample s;
    int bails = 0, finished = 0;
    double bail_time = -1;
    Result last;
    // Move every bone centre by velocity v (m/s) for `seconds`, with the given state flags.
    // `fall` adds gravity to v[1] as time goes (free fall).
    void run(double seconds, std::array<float, 3> v, std::uint32_t state, bool upright, bool lying, float speed = -1, bool fall = false) {
        const double dt = 1.0 / 60.0;
        for (double e = 0; e < seconds; e += dt) {
            time += dt;
            if (fall) v[1] -= 9.81f * static_cast<float>(dt);
            s.time = time;
            s.physics_state = state;
            s.upright = upright;
            s.lying = lying;
            s.bones_valid = true;
            for (auto &c : s.bone_centres)
                for (int k = 0; k < 3; ++k) c[k] += v[k] * static_cast<float>(dt);
            for (int k = 0; k < 3; ++k) s.position[k] += v[k] * static_cast<float>(dt);
            s.speed = speed >= 0 ? speed : std::sqrt(v[0] * v[0] + v[2] * v[2]);
            const auto before = t.phase();
            if (t.update(s)) {
                ++finished;
                last = t.result();
            }
            if (before != Phase::bailing && t.phase() == Phase::bailing) {
                ++bails;
                if (bail_time < 0) bail_time = time;
            }
        }
    }
};

int check(const char *name, bool ok) {
    std::printf("%s %s\n", ok ? "PASS" : "FAIL", name);
    return ok ? 0 : 1;
}

int main() {
    int failures = 0;
    {   // Glide: off the board, body horizontal, sailing at 7 m/s and sinking, then landing on the feet.
        Sim m;
        m.run(1.0, {0, 0, 7}, 100, true, false);
        m.run(3.0, {0, -2, 7}, 504, false, true);   // gliding: lying, smooth
        m.run(0.05, {0, 0, 1}, 504, false, false);  // touchdown: sudden stop, crouched
        m.run(1.0, {0, 0, 0}, 504, true, false);    // standing
        failures += check("glide ending on the feet starts no bail", m.bails == 0);
    }
    {   // Slam: off the board into a fall, hit the ground hard, lie there, then get up.
        Sim m;
        m.run(1.0, {0, 0, 7}, 100, true, false);
        m.run(0.8, {0, -9, 6}, 504, false, true);   // falling, body down
        m.run(1.5, {0, 0, 0.5}, 504, false, true);  // slammed: stopped dead, sliding a little
        m.run(3.0, {0, 0, 0}, 504, false, true);    // lying still
        m.run(1.0, {0, 0, 0}, 504, true, false);    // up
        failures += check("slam starts a bail", m.bails == 1);
        failures += check("slam bail finishes when standing", m.finished == 1);
        failures += check("score stops once still (duration < 2.6 s)", m.last.duration < 2.6f && m.last.duration > 0.8f);
        failures += check("impact before recognition damages bones", m.last.bone_points > 0);
        std::printf("     duration %.2f s, broken %zu, bone points %d, total %d\n", m.last.duration, m.last.broken.size(), m.last.bone_points, m.last.total);
    }
    {   // Glide with a jolt in the air (leaving the board, steering): no bail until it lands.
        Sim m;
        m.run(1.0, {0, 0, 9}, 100, true, false);
        m.run(0.4, {0, -3, 9}, 504, false, true);
        m.run(0.05, {0, -3, 3}, 504, false, true);  // jolt: lost 6 m/s at once, still in the air
        m.run(2.0, {0, -4, 4}, 504, false, true);   // keeps gliding down
        failures += check("glide jolt in the air starts no bail", m.bails == 0);
        m.run(0.05, {0, 0, 0.3}, 504, false, true); // belly flop
        m.run(1.0, {0, 0, 0.2}, 504, false, true);
        failures += check("glide ending in a belly flop starts a bail", m.bails == 1);
    }
    {   // Wipeout state: immediate.
        Sim m;
        m.run(1.0, {0, 0, 7}, 100, true, false);
        m.run(0.1, {0, 0, 7}, 300, false, false);
        failures += check("wipeout state starts at once", m.bails == 1);
    }
    {   // Hippy jump: off the board for a moment, upright, lands on the feet.
        Sim m;
        m.run(1.0, {0, 0, 7}, 100, true, false);
        m.run(0.6, {0, 2, 7}, 504, true, false);
        m.run(0.05, {0, 0, 2}, 504, true, false);
        m.run(0.5, {0, 0, 7}, 100, true, false);
        failures += check("hippy jump starts no bail", m.bails == 0);
    }
    {   // Lying still the whole time after a crash keeps the X-ray (no finish) until standing.
        Sim m;
        m.run(1.0, {0, 0, 7}, 100, true, false);
        m.run(0.1, {0, 0, 7}, 300, false, true);
        m.run(0.3, {0, 0, 0}, 504, false, true);
        m.run(6.0, {0, 0, 0}, 504, false, true);
        failures += check("still body does not end the bail", m.finished == 0 && m.t.phase() == Phase::bailing);
        failures += check("score frozen while still", m.t.live().duration < 1.2f);
    }
    {   // A long fall onto the ground: hard enough to break bones by Skate 3's table.
        Sim m;
        m.run(1.0, {0, 0, 7}, 100, true, false);
        m.run(1.5, {0, -22, 2}, 504, false, true);
        m.run(1.0, {0, 0, 0}, 504, false, true);
        failures += check("22 m/s slam breaks bones", !m.t.live().broken.empty());
        std::printf("     broken %zu, bone points %d\n", m.t.live().broken.size(), m.t.live().bone_points);
    }
    {   // Getting up and running off ends the bail at once, even at a run.
        Sim m;
        m.run(1.0, {0, 0, 7}, 100, true, false);
        m.run(0.8, {0, -9, 6}, 504, false, true);
        m.run(1.5, {0, 0, 0.5}, 504, false, true);
        m.run(1.0, {0, 0, 5}, 504, true, false); // up and running at 5 m/s
        failures += check("standing up while running ends the bail", m.finished == 1);
    }
    {   // A dive off a ramp (off the board in the air): gliding fast and low, steering jolts, no bail.
        Sim m;
        m.run(1.0, {0, 0, 15}, 100, true, false);
        m.run(0.5, {0, 3, 15}, 201, true, false);   // in the air on the board
        m.run(0.6, {0, -1, 40}, 504, false, true);  // dive: flat out at 40 m/s, sinking slowly
        m.run(0.05, {0, -1, 33}, 504, false, true); // a jolt
        m.run(1.0, {0, -1, 38}, 504, false, true);
        failures += check("a fast dive with jolts starts no bail", m.bails == 0);
    }
    {   // Jumping off the board in the air and coming down hard (a Heavy Slam): a bail.
        Sim m;
        m.run(1.0, {0, 0, 10}, 100, true, false);
        m.run(0.5, {0, 3, 10}, 201, true, false);
        m.run(0.7, {0, -8, 6}, 504, false, true);   // off the board, falling
        m.run(0.05, {0, 0, 0.5}, 504, false, true); // lands
        m.run(1.0, {0, 0, 0.2}, 504, false, true);
        failures += check("jumping off in the air and slamming down starts a bail", m.bails == 1);
    }
    {   // Getting up after the body stopped does not count on.
        Sim m;
        m.run(1.0, {0, 0, 7}, 100, true, false);
        m.run(0.1, {0, 0, 7}, 300, false, true);
        m.run(3.0, {0, 0, 0}, 504, false, true);
        const float before = m.t.live().duration;
        m.run(0.3, {0, 0, 3}, 504, false, false);   // getting up: moving, not yet upright
        failures += check("getting up keeps the score frozen", m.t.live().duration == before);
    }
    {   // Falling off a big ramp and smashing down: Hall of Meat starts on the impact, and the fall counts.
        Sim m;
        m.run(1.0, {0, 0, 7}, 100, true, false);
        m.run(0.2, {0, 0, 7}, 201, true, false);
        m.run(2.0, {0, 0, 5}, 504, false, false, -1, true); // free fall for 2 s (~20 m)
        const double impact = m.time;
        m.run(0.05, {0, 0, 0.3}, 504, false, false);        // smash, not lying flat yet
        m.run(1.0, {0, 0, 0}, 504, false, true);
        failures += check("a hard slam starts Hall of Meat at the impact", m.bail_time >= 0 && m.bail_time - impact < 0.06);
        failures += check("the fall before the slam counts as air and drop", m.t.live().air_time > 1.5f && m.t.live().drop > 15.0f);
        std::printf("     started %.3f s after impact, air %.2f s, drop %.1f m\n", m.bail_time - impact, m.t.live().air_time, m.t.live().drop);
    }
    {   // Sliding down a steep ramp during a bail is not air.
        Sim m;
        m.run(1.0, {0, 0, 7}, 100, true, false);
        m.run(0.1, {0, 0, 7}, 300, false, true);
        m.run(3.0, {0, -8, 8}, 504, false, true);
        failures += check("sliding down a ramp is not air", m.t.live().air_time < 0.2f);
    }
    {   // Walking off a ledge into a dive: slow and level at the top of the jump, in free fall. No bail
        // at the top, nor while diving down fast.
        Sim m;
        m.run(1.0, {0, 0, 1}, 504, true, false);         // walking off the board
        m.run(0.5, {0, 3, 3}, 504, false, true, -1, true); // up and over the top, flat out, falling
        m.run(0.05, {0, -2, 1}, 504, false, true);         // a jolt near the top
        m.run(0.5, {0, -6, 20}, 504, false, true);         // diving down fast
        failures += check("a jump into a dive starts no bail at its top", m.bails == 0);
    }
    {   // A dive that sinks fast and brushes something keeps flying: no slam.
        Sim m;
        m.run(1.0, {0, 0, 12}, 100, true, false);
        m.run(0.3, {0, 2, 12}, 201, true, false);
        m.run(0.5, {0, -7, 12}, 504, false, true);
        m.run(0.05, {0, -7, 10}, 504, false, true);  // brushes something
        m.run(0.5, {0, -7, 12}, 504, false, true);
        failures += check("a fast dive that brushes something is no slam", m.bails == 0);
    }
    {   // HOM test 15 at 18.6 s: a dive off the board, speeding up and sinking at 5-8 m/s, with a jolt.
        Sim m;
        m.run(1.0, {0, 0, 12}, 100, true, false);
        m.run(0.3, {0, 2, 12}, 201, true, false);
        m.run(0.6, {0, -5, 17}, 504, false, true);
        m.run(0.6, {0, -8, 28}, 504, false, true);
        m.run(0.05, {0, -8, 12}, 504, false, true); // jolt: 16 m/s gone in a tick
        m.run(0.5, {0, -8, 29}, 504, false, true);
        failures += check("test 15: a sinking dive with a jolt is no slam", m.bails == 0);
    }
    {   // HOM test 15 at 39 s: walking off a ledge with a jump into a spread eagle; a jolt on the way up.
        Sim m;
        m.run(1.0, {0, 0, 1}, 504, true, false);
        for (int i = 0; i < 11; i++) m.run(0.05, {0, 7.8f - 9.81f * 0.05f * i, 15}, 504, false, true); // up, slowing at g
        m.run(0.05, {0, 1.5f, 1}, 504, false, true);                                                   // jolt near the top
        for (int i = 0; i < 8; i++) m.run(0.05, {0, 1.0f - 9.81f * 0.05f * i, 5}, 504, false, true);
        failures += check("test 15: a jolt at the top of a jump is no bail", m.bails == 0);
    }
    {   // HOM test 16 at 27.7 s: knocked off the board while riding down a ramp (a Harsh Slam), then
        // sliding down it: Hall of Meat starts as the board goes, not after the slide.
        Sim m;
        m.run(1.0, {0, -1, 9}, 100, true, false);
        m.run(0.017, {0, -3.7f, 1}, 504, false, true);  // the hit as the board goes
        const double off = m.time;
        m.run(1.5, {0, -8, 4}, 504, false, true);       // sliding down the ramp
        failures += check("test 16: knocked off the board starts at once", m.bail_time >= 0 && m.bail_time - off < 0.1);
    }
    {   // HOM test 16 at 62.3 s: coming down from a big air onto the ramp at 20 m/s, sliding on.
        Sim m;
        m.run(1.0, {0, 0, 8}, 100, true, false);
        m.run(1.5, {0, -20, 3}, 201, false, true);      // in the air on the board, falling
        m.run(0.017, {0, -14, 8}, 504, false, true);    // lands on the ramp: off the board, a small hit
        const double off = m.time;
        m.run(1.5, {0, -10, 8}, 504, false, true);
        failures += check("test 16: crashing down onto a ramp starts at once", m.bail_time >= 0 && m.bail_time - off < 0.1);
    }
    {   // HOM test 16 at 44.2 s: starting a dive while falling at 8 m/s: no bail.
        Sim m;
        m.run(1.0, {0, 0, 8}, 100, true, false);
        m.run(1.0, {0, -8, 8}, 201, false, true);
        m.run(1.0, {0, -8, 8}, 504, false, true);
        failures += check("test 16: a dive started while falling is no bail", m.bails == 0);
    }
    {   // A big dive started late in a long fall (17 m/s down, nothing hit): no bail.
        Sim m;
        m.run(1.0, {0, 0, 8}, 100, true, false);
        m.run(1.0, {0, -17, 8}, 201, false, true);
        m.run(0.6, {0, -17, 8}, 504, false, true);
        failures += check("a dive late in a long fall is no bail", m.bails == 0);
    }
    {   // A hippy jump: off the board upright, no hit: no bail.
        Sim m;
        m.run(1.0, {0, 0, 8}, 100, true, false);
        m.run(0.5, {0, 2, 8}, 504, true, false);
        failures += check("a hippy jump off the board is no bail", m.bails == 0);
    }
    {   // HOM test 17 at 3.4 s: off the board after a plant, onto a ledge at 5 m/s down; the pose jumps
        // the next tick. No Hall of Meat until the skater really falls.
        Sim m;
        m.run(1.0, {0, 0, 9}, 100, true, false);
        m.run(0.4, {0, -5, 9}, 201, false, false);
        m.run(1.0 / 60, {0, -5, 9}, 504, false, false);   // off the board
        m.run(1.0 / 60, {0, -9, 0.5f}, 504, false, false); // the pose switches over: the bones jump down
        m.run(0.12, {0, 0, 0.5f}, 504, false, false);       // crouched on the ledge
        failures += check("test 17: coming off the board onto a ledge is no slam", m.bails == 0);
        m.run(0.5, {0, -2, 2}, 504, false, true, -1, true); // then really falls off the ledge
        m.run(0.05, {0, 0, 0.3f}, 504, false, true);         // and smashes down
        m.run(1.0, {0, 0, 0}, 504, false, true);
        failures += check("test 17: the real fall after it still starts Hall of Meat", m.bails == 1);
    }
    {   // HOM test 20 at 26-29.5 s: a jump off the board into a spread-eagle glide, landing with a jolt,
        // straight back on the board: never shown.
        Sim m;
        m.run(1.0, {0, 0, 7}, 100, true, false);
        m.run(0.3, {0, 5, 11}, 504, true, false);         // jumps off
        m.run(1.2, {0, -4, 16}, 504, false, true);        // gliding flat out
        m.run(0.4, {0, -7, 20}, 504, false, true);
        bool shown = false;
        for (int i = 0; i < 3; ++i) { m.run(1.0 / 60, {0, -1, 6}, 504, false, true); shown = shown || m.t.showing(); } // lands
        for (int i = 0; i < 30; ++i) { m.run(1.0 / 60, {0, 0, 5}, 504, false, true); shown = shown || m.t.showing(); }
        m.run(0.3, {0, 0, 5}, 103, true, false);           // back on the board
        failures += check("test 20: a glide's landing is never shown as a crash", !shown && m.t.cancelled() == 1 && m.t.phase() != Phase::bailing);
    }
    {   // A glide that ends in a real smash (the skater stays down): shown, a little later.
        Sim m;
        m.run(1.0, {0, 0, 7}, 100, true, false);
        m.run(0.3, {0, 5, 11}, 504, true, false);
        m.run(1.2, {0, -4, 16}, 504, false, true);
        m.run(0.4, {0, -7, 20}, 504, false, true);
        m.run(0.05, {0, 0, 0.3f}, 504, false, true);       // smashes into the ground
        m.run(1.5, {0, 0, 0}, 504, false, true);           // and lies there
        failures += check("a glide that ends in a smash is shown once the skater stays down", m.t.showing());
    }
    {   // Crash, then keep tumbling off an edge feet first: upright but still dropping is not getting up.
        Sim m;
        m.run(1.0, {0, 0, 7}, 100, true, false);
        m.run(0.1, {0, 0, 7}, 300, false, true);
        m.run(0.6, {0, 0, 1}, 504, false, true);
        m.run(1.2, {0, -1, 1}, 504, true, false, -1, true); // upright, falling
        failures += check("upright while still falling does not end the bail", m.finished == 0 && m.t.phase() == Phase::bailing);
    }
    {   // Mid-tumble the state flicks to the board for a few ticks: the bail carries on.
        Sim m;
        m.run(1.0, {0, 0, 7}, 100, true, false);
        m.run(0.1, {0, 0, 7}, 300, false, true);
        m.run(0.5, {0, -3, 3}, 504, false, true);
        m.run(0.15, {0, -3, 3}, 201, false, false);
        m.run(0.5, {0, -3, 3}, 504, false, true);
        failures += check("a flick back to the board mid-tumble does not end the bail", m.finished == 0 && m.t.phase() == Phase::bailing);
    }
    {   // Crash, stand for a moment, then go straight down a drop: one continuous bail.
        Sim m;
        m.run(1.0, {0, 0, 7}, 100, true, false);
        m.run(0.8, {0, -9, 6}, 504, false, true);
        m.run(1.5, {0, 0, 0.5}, 504, false, true);
        m.run(0.6, {0, 0, 0}, 504, true, false);           // up (the bail ends)
        const auto first = m.last.serial;
        const int bones_before = m.last.bone_points;
        m.run(0.8, {0, -9, 2}, 504, false, true);          // falls off the edge
        m.run(0.05, {0, 0, 0.3f}, 504, false, true);       // lands hard again
        m.run(1.0, {0, 0, 0}, 504, false, true);
        failures += check("a second drop straight after carries on the same bail",
                          m.finished == 1 && m.t.phase() == Phase::bailing && m.t.live().serial == first && m.t.carried_on() &&
                              m.t.live().bone_points >= bones_before);
    }
    {   // Leaving the board in the air: the pose snaps over and flings only the hands and feet, then
        // the skater lands on their back. The hands and feet must not show the snap as breaks.
        Sim m;
        m.run(1.0, {0, 0, 7}, 100, true, false);
        m.run(0.4, {0, 3, 7}, 201, true, false);
        m.run(1.0 / 60, {0, 1, 7}, 504, false, false);
        for (int i : {9, 10, 15, 16, 17, 18}) m.s.bone_centres[i][2] -= 0.5f; // limbs jump back while the torso flies on
        m.run(1.0 / 60, {0, 1, 7}, 504, false, false);
        for (int i : {9, 10, 15, 16, 17, 18}) m.s.bone_centres[i][2] += 0.5f;
        m.run(1.0 / 60, {0, 1, 7}, 504, false, false);
        m.run(0.5, {0, 0, 6}, 504, false, true, -1, true);
        m.run(0.05, {0, 0, 1}, 504, false, true);           // lands on the back
        m.run(1.5, {0, 0, 0}, 504, false, true);
        float limbs = 0;
        for (int i : {9, 10, 15, 16, 17, 18}) limbs = std::max(limbs, m.t.live().damage[i]);
        std::printf("     bails %d, hands/feet damage %.2f, torso %.2f\n", m.bails, limbs, m.t.live().damage[2]);
        failures += check("leaving the board mid-air does not break the hands and feet", m.bails == 1 && limbs <= m.t.live().damage[2] + 0.01f);
    }
    {   // Skate 3's car bonus: hit by a car, 2,000; touching it on the next ticks pays nothing more.
        Sim m;
        m.run(1.0, {0, 0, 7}, 100, true, false);
        m.s.vehicle = true;
        m.run(0.1, {0, 0, 7}, 300, false, true);
        m.run(0.3, {0, 0, 3}, 504, false, true);
        m.s.vehicle = false;
        m.run(1.6, {0, 0, 0}, 504, false, true);
        const bool one = m.t.live().car_count == 1 && m.t.live().car_points == 2000;
        m.s.vehicle = true;                              // a second car, later
        m.run(0.1, {0, 0, 0}, 504, false, true);
        m.s.vehicle = false;
        m.run(0.5, {0, 0, 0}, 504, false, true);
        std::printf("     cars %d points %d\n", m.t.live().car_count, m.t.live().car_points);
        failures += check("car bonus: 2,000 a car, apart by its gap", one && m.t.live().car_count == 2 && m.t.live().car_points == 4000);
    }
    {   // Trainer-boosted jump off the board (11 m/s up) into a glide, landing in a long belly slide
        // before popping back up: never shown.
        Sim m;
        m.run(1.0, {0, 0, 8}, 100, true, false);
        m.run(0.2, {0, 11.2f, 8}, 201, true, false, -1, true);
        m.run(0.4, {0, 9.0f, 9}, 504, true, false, -1, true);
        m.run(0.05, {0, 0, 4}, 504, false, true);
        bool shown = false;
        for (int i = 0; i < 132; ++i) { m.run(1.0 / 60, {0, -5, 12}, 504, false, true); shown = shown || m.t.showing(); }
        m.run(1.0 / 20, {0, -1, 6}, 504, false, true);
        for (int i = 0; i < 72; ++i) { m.run(1.0 / 60, {0, 0, 5}, 504, false, true); shown = shown || m.t.showing(); }
        m.run(0.5, {0, 0, 5}, 103, true, false);
        failures += check("a boosted glide's long belly slide is never shown as a crash", !shown && m.t.phase() != Phase::bailing);
    }
    {   // Session log 19:37:12: a boosted jump, then jumping off the board mid-air while dropping at
        // 13 m/s (the pose snaps over), and gliding on down: never shown.
        Sim m;
        m.run(1.0, {0, 0, 9}, 100, true, false);
        m.run(1.2, {0, 14.5f, 12}, 201, true, false, -1, true);  // up and over the top, dropping fast
        m.run(1.0 / 60, {0, -13.5f, 12}, 504, false, false);
        for (int i : {9, 10, 15, 16, 17, 18}) m.s.bone_centres[i][2] -= 0.3f; // the snap
        bool shown = false;
        for (int i = 0; i < 90; ++i) { m.run(1.0 / 60, {0, -6, 14}, 504, false, true); shown = shown || m.t.showing(); }
        failures += check("log 19:37: jumping off the board mid-air into a glide is never shown", !shown);
    }
    {   // A jolt mid-glide that looks like a slam (the fall stops for a tick or two), then gliding on.
        Sim m;
        m.run(1.0, {0, 0, 9}, 100, true, false);
        m.run(0.6, {0, 10, 11}, 201, true, false, -1, true);
        m.run(1.0 / 60, {0, 4, 11}, 504, true, false);
        m.run(0.5, {0, -9, 14}, 504, false, true);
        m.run(2.0 / 60, {0, -0.5f, 4}, 504, false, true);         // the jolt
        bool shown = false;
        for (int i = 0; i < 60; ++i) { m.run(1.0 / 60, {0, -5, 12}, 504, false, true); shown = shown || m.t.showing(); }
        failures += check("a slam-like jolt mid-glide is never shown", !shown);
        m.run(0.05, {0, 0, 0.3f}, 504, false, true);               // then really smashes down
        m.run(1.0, {0, 0, 0}, 504, false, true);
        failures += check("the glide's real smash afterwards is shown", m.t.showing());
    }
    {   // A real crash landing: dropping fast off a jump, the board goes and the body hits the ground.
        Sim m;
        m.run(1.0, {0, 0, 9}, 100, true, false);
        m.run(0.8, {0, -13, 9}, 201, true, false);
        m.run(1.0 / 60, {0, -13, 9}, 504, false, false);
        m.run(1.0 / 60, {0, 0, 3}, 504, false, true);              // hits the ground
        m.run(0.6, {0, 0, 1}, 504, false, true);
        std::printf("     bails %d phase %d cancelled %d trig %s\n", m.bails, (int)m.t.phase(), m.t.cancelled(), m.t.trigger().c_str());
        failures += check("a real crash landing from the air is shown within 0.6 s", m.t.showing());
    }
    {   // HOM test 22 at 36.1 s: a crash landing head first. The board goes as the skull hits; the
        // torso slides on. Shown at once, and the skull is hurt (it showed no bones at all).
        Sim m;
        m.run(1.0, {0, 0, 9}, 100, true, false);
        m.run(0.8, {0, -13, 9}, 201, true, false);
        const double impact = m.time;
        m.s.bone_centres[0][1] += 13.0f / 60; m.s.bone_centres[0][2] -= 9.0f / 60;   // the skull stops dead as
        m.s.bone_centres[1][1] += 13.0f / 60; m.s.bone_centres[1][2] -= 9.0f / 60;   // the board goes
        m.run(1.0 / 60, {0, -13, 9}, 504, false, false);
        m.run(1.0 / 60, {0, 0, 6}, 504, false, true);
        double shown_at = -1;
        for (int i = 0; i < 60; ++i) { m.run(1.0 / 60, {0, 0, 2}, 504, false, true); if (shown_at < 0 && m.t.showing()) shown_at = m.time; }
        std::printf("     shown %.2f s after impact (%s), skull damage %.2f, bone points %d\n", shown_at - impact, m.t.trigger().c_str(), m.t.live().damage[0], m.t.live().bone_points);
        failures += check("test 22: a head-first crash landing shows at once", shown_at >= 0 && shown_at - impact < 0.12);
        failures += check("test 22: a head-first crash landing hurts the skull", m.t.live().damage[0] > 0 && m.t.live().bone_points > 0);
    }
    {   // HOM test 24 at 3.5 s: a jump into a spread-eagle glide that ends in a heavy slam, the body
        // stopped dead: shown at once (it took 0.6 s).
        Sim m;
        m.run(1.0, {0, 0, 7}, 100, true, false);
        m.run(0.3, {0, 5, 11}, 504, true, false);
        m.run(1.2, {0, -4, 16}, 504, false, true);
        m.run(0.4, {0, -9, 18}, 504, false, true);
        const double impact = m.time;
        m.run(0.05, {0, 0, 0.5f}, 504, false, true);
        double shown_at = -1;
        for (int i = 0; i < 60; ++i) { m.run(1.0 / 60, {0, 0, 0.3f}, 504, false, true); if (shown_at < 0 && m.t.showing()) shown_at = m.time; }
        std::printf("     glide slam shown %.2f s after impact\n", shown_at - impact);
        failures += check("test 24: a glide ending in a slam shows within 0.3 s", shown_at >= 0 && shown_at - impact < 0.3);
    }
    {   // Session 21:29: a heavy slam landing on a slope, the ragdoll sliding on downhill. skate. calls
        // it a ragdoll: shown, never taken back as a glide.
        Sim m;
        m.run(1.0, {0, 0, 9}, 100, true, false);
        m.run(0.8, {0, -15, 12}, 201, true, false);
        m.s.ragdoll = 1;
        m.s.bone_centres[0][1] += 15.0f / 60;
        m.run(1.0 / 60, {0, -15, 12}, 504, false, true);
        m.run(1.0 / 60, {0, -4, 6}, 504, false, true);
        bool shown = false;
        for (int i = 0; i < 60; ++i) { m.run(1.0 / 60, {0, -3.5f, 6}, 504, false, true); shown = shown || m.t.showing(); }
        failures += check("a ragdoll sliding down a slope after a crash landing is shown", shown && m.t.cancelled() == 0);
        m.s.ragdoll = -1;
    }
    {   // The same glide jolt as before, with skate. saying it is no ragdoll: still never shown.
        Sim m;
        m.s.ragdoll = 0;
        m.run(1.0, {0, 0, 9}, 100, true, false);
        m.run(0.6, {0, 10, 11}, 201, true, false, -1, true);
        m.run(1.0 / 60, {0, 4, 11}, 504, true, false);
        m.run(0.5, {0, -9, 14}, 504, false, true);
        m.run(2.0 / 60, {0, -0.5f, 4}, 504, false, true);
        bool shown = false;
        for (int i = 0; i < 60; ++i) { m.run(1.0 / 60, {0, -5, 12}, 504, false, true); shown = shown || m.t.showing(); }
        failures += check("a jolt mid-glide (no ragdoll) is never shown", !shown);
    }
    // Skate 3's graphs against the original's HUD readings.
    failures += check("bail 7.10 s pays 7,750", metric_points(3, 7.10f) == 7750);
    failures += check("drop 31.5 m pays ~5,750", std::abs(metric_points(2, 31.5f) - 5750) <= 10);
    failures += check("speed 65.5 km/h pays ~6,383", std::abs(metric_points(4, 65.5f / 3.6f) - 6383) <= 15);
    failures += check("air 6.4 s caps at 10,000", metric_points(1, 6.4f) == 10000);
    std::printf("%d failure(s)\n", failures);
    return failures;
}
