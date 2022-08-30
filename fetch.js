const simpleGit = require('simple-git');
const git = simpleGit();
const fs = require("fs"); // Or `import fs from "fs";` with ESM
const util = require('util')
const path = require("path")
const yaml = require('js-yaml');
const yargs = require('yargs/yargs')
const { hideBin } = require('yargs/helpers')

// optional playbook arg
const argv = yargs(hideBin(process.argv))
  .alias('p', 'playbookFile')
  .argv

// this file is in branch 4.2 or a branch created from 4.2 (eg a PR branch)
const workingBranch = '4.2'

// use preview.yml as the default playbook
let playbookFile = path.join(__dirname, (argv.playbookFile || 'preview.yml'))

// check for existing clone
async function isRoot(localPath) {
  return await git.cwd(localPath).checkIsRepo('root')
}

// clone a thing
async function doClone(repoPath,localPath,apiVersion) {
  let result = null
  try {
    console.log(`Cloning ${repoPath} branch ${apiVersion} to ${localPath}`)
    const result = await git.clone(repoPath,localPath).cwd(localPath).checkout(apiVersion)
    return result
  }
  catch(e) {
    console.log(e)
  }
  finally {
    // finally nothing
  }

  
}

async function status (localPath) {
  console.log(localPath)
  let statusSummary = null
  try {
     statusSummary = await git(localPath).status()
  }
  catch (e) {
     // handle the error
  }
  
  return statusSummary
}

const playbook = yaml.load(fs.readFileSync(playbookFile, 'utf8'))

const sourceBranches = playbook.content.sources.map( function (source) { return source.branches } ).flat()

// const sourceBranches = playbook.content.sources[0].branches
const startPaths = playbook.content.sources[0].start_paths

// get a list of driver languages in this playbook
const langIdentifier = '-manual'
const langs = startPaths.filter( startPath => startPath.includes('-manual')).map( lang => lang.replace(langIdentifier,''))

console.log(`Branches in playbook: ${sourceBranches}`)
console.log(`Driver languages in playbook: ${langs}`)

langs.forEach (function(lang) {

  sourceBranches.forEach (function(branch) {

    let worktreeBranch = branch == 'HEAD' ? workingBranch : branch
    let branchPath = (playbook.asciidoc.attributes["neo4j-version"].includes(worktreeBranch))  ? path.join(__dirname) : path.join(__dirname, 'worktrees', worktreeBranch)
    
    let langPath, clonePath, antoraYMLFile

    // get a path to clone the api examples into
    
    switch (worktreeBranch) {
      case '4.1':
      case '4.0':
      case '1.7':
        antoraYMLFile = path.join(branchPath,'antora.yml')
        clonePath = path.join(branchPath, "modules", "ROOT", "partials", "driver-sources", lang + "-driver")
        break;
      default:
        langPath = path.join(branchPath, lang + "-manual")
        antoraYMLFile = path.join(langPath,'antora.yml')
        clonePath = path.join(langPath, "modules", "api", "examples")
    }

    // get the api version for this lang from antora.yml
    // every antora.yml needs to have a <LANG>-driver-apidoc-version
    // this attribute does what the old driver version mapping json file did
    const descriptor = yaml.load(fs.readFileSync(antoraYMLFile, 'utf8'))
    const apiVersion = descriptor.asciidoc.attributes[`${lang}-driver-apidoc-version`]
    const apiExamples = descriptor.asciidoc.attributes[`${lang}-examples`]
    
    // the api repo to clone so we have the example code
    const repo = 'https://github.com/neo4j/neo4j-'+lang+'-driver.git'
        
    if (fs.existsSync(clonePath)) {
      fs.rmSync(clonePath, { recursive: true })
    }
    
    fs.mkdirSync(clonePath, { recursive: true })


    try {
      const cloneResult = doClone(repo,clonePath,apiVersion)
      .then(function(cloneResult) {
        console.log(`-----\nManual: ${lang}-manual, github branch ${branch}`)
        console.log(`The apiVersion is ${apiVersion}, Antora path to examples is ${apiExamples}`)
        console.log(`API examples are checked out in ${clonePath}`)
        console.log(`Git result: ${cloneResult}-----\n`) // "Some User token"
      })
    } catch (e) {
        console.log(e)
    } finally {
        // finally nothing
    }

  })

})
