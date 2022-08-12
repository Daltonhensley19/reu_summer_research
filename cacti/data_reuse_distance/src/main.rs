#![warn(clippy::perf)]

use clap::ArgEnum;
use clap::Parser;
use regex::Regex;

use std::collections::BTreeMap;
use std::collections::BTreeSet;
use std::collections::HashSet;
use std::fs;
use std::io::prelude::*;
use std::path::Path;
use std::process::Command;

#[derive(Debug, Clone, Copy, ArgEnum, PartialEq)]
enum Mode {
    Data,
    Ref,
}

#[derive(Parser, Debug)]
struct Args {
    /// Name of the person to greet
    #[clap(short, long)]
    plot: bool,

    #[clap(arg_enum)]
    mode: Mode,
}

fn vec_to_set(vec: Vec<usize>) -> HashSet<usize> {
    HashSet::from_iter(vec)
}

type ReuseDist = (Vec<(usize, Option<usize>)>, bool);

fn calculate_reuse_dist(vec: &[usize]) -> ReuseDist {
    let mut reuse_vec: Vec<(usize, Option<usize>)> = Vec::new();

    let mut meta_tree = BTreeMap::new();
    let mut history_tree = BTreeSet::new();

    let mut has_reuse_dist = false;
    let increment_some = |a, b| a + b;

    for i in 0..vec.len() {
        let mut dist = Some(0);

        let meta_value = &vec[i];
        let meta_index = i;

        //dbg!(&history_tree);

        if !meta_tree.contains_key(&vec[i]) {
            meta_tree.insert(&vec[i], meta_index);
            reuse_vec.push((vec[i], None));
            continue;
        } else {
            has_reuse_dist = true;
            let sweep_dist = meta_tree[&vec[i]];
            meta_tree.remove(&vec[i]);
            meta_tree.insert(&vec[meta_index], meta_index);

            for sweep_idx in sweep_dist + 1..i {
                history_tree.insert(vec[sweep_idx]);
            }

            for _ in &history_tree {
                dist = dist.and_then(|a| Some(1).map(|b| increment_some(a, b)));
            }

            history_tree.clear();
            reuse_vec.push((*meta_value, dist));
        }
    }
    (reuse_vec, has_reuse_dist)
}
fn calculate_avg_reuse(vec: &Vec<(usize, Option<usize>)>) -> f32 {
    let mut total_dist = 0.0;
    
    let mut some_count = 0;
    for (_addr, dist) in vec {
        if let Some(d) = dist {
            total_dist += *d as f32;
            some_count += 1;
        }  
    }

    total_dist / some_count as f32
}

fn main() {
    let args = Args::parse();

    // Create regular expr for memory accesses and data
    let addr_regex = Regex::new(r"Data Index: (\d*)").unwrap();
    let data_regex = Regex::new(r"Data: (\d*)").unwrap();

    // Extract file for processing
    let file_path = Path::new("../reuse_dist_analysis.txt");
    let reuse_analysis_file = fs::read_to_string(file_path).unwrap();

    //println!("{}", reuse_analysis_file);

    // Capture references using regex
    let mut references_buffer: Vec<usize> = Vec::new();
    for cap in addr_regex.captures_iter(&reuse_analysis_file) {
        let addr = cap[1].to_owned();
        let addr = addr.parse::<usize>().unwrap();
        references_buffer.push(addr);
    }

    // Capture data using regex
    let mut data_buffer: Vec<usize> = Vec::new();
    for cap in data_regex.captures_iter(&reuse_analysis_file) {
        let data = cap[1].to_owned();
        let data = data.parse::<usize>().unwrap();
        data_buffer.push(data);
    }

    let test_buffer = vec![1, 2, 4, 3, 3, 2, 2, 2, 3];

    let (reuse_vec_ref, has_reuse_dist_ref) = calculate_reuse_dist(&references_buffer);
    let (reuse_vec_data, has_reuse_dist_data) = calculate_reuse_dist(&data_buffer);

    let mut reuse_file = fs::File::create("rust_reuse.txt").unwrap();

    if args.mode == Mode::Ref {
        for (addr, dist) in &reuse_vec_ref {
            println!("Addr: {:#04X}\t\tDist: {:?}", addr, dist);
            reuse_file
                .write(format!("Addr: {addr:#04X}\t\tDist: {dist:?}\n").as_bytes())
                .unwrap();
        }

        let avg_dist = calculate_avg_reuse(&reuse_vec_ref);

        println!(
            "\nAverage distance with which an address is reused: {:.3}",
            avg_dist
        );

        let plot_enabled = args.plot;

        if plot_enabled {
            if has_reuse_dist_ref {
                let _plotting_proc = Command::new("python3")
                    .arg("reuse_graph.py")
                    .arg("-m")
                    .arg("ref")
                    .spawn()
                    .unwrap();
            } else {
                println!("ERROR: Plotting is disabled due to no address reuse");
            }
        }
    } else {
        for (data, dist) in &reuse_vec_data {
            println!("Addr: {:#04X}\t\tDist: {:?}", data, dist);
            reuse_file
                .write(format!("Data: {data:#04X}\t\tDist: {dist:?}\n").as_bytes())
                .unwrap();
        }

        let avg_dist = calculate_avg_reuse(&reuse_vec_data);

        println!(
            "\nAverage distance with which data is reused: {:.3}",
            avg_dist
        );

        let plot_enabled = args.plot;

        if plot_enabled {
            if has_reuse_dist_data {
                let _plotting_proc = Command::new("python3")
                    .arg("reuse_graph.py")
                    .arg("-m")
                    .arg("data")
                    .spawn()
                    .unwrap();
            } else {
                println!("ERROR: Plotting is disabled due to no address reuse");
            }
        }
    }

    if args.mode == Mode::Ref {
        println!(
            "Total number of addresses accessed: {}",
            references_buffer.len()
        );

        let ref_len = references_buffer.len();
        let references_buffer_unique = vec_to_set(references_buffer);

        let unique_percent = (references_buffer_unique.len() as f32 / ref_len as f32) * 100.0;

        println!(
            "Total number of unique addresses accessed: {}  ({}%  lower is better)",
            references_buffer_unique.len(),
            unique_percent
        );
    } else if args.mode == Mode::Data {
        println!("Total number of data accesses: {}", data_buffer.len());

        let data_len = data_buffer.len();
        let data_buffer_unique = vec_to_set(data_buffer);

        let unique_percent = (data_buffer_unique.len() as f32 / data_len as f32) * 100.0;

        println!(
            "Total number of unique data accesses: {} ({}% lower is better)",
            data_buffer_unique.len(),
            unique_percent
        );
    }
}
